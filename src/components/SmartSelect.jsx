import { useState, useEffect, useRef } from "react";

// Detects Apple platform once — Safari, iOS, macOS
function isApplePlatform() {
  return /Mac|iPhone|iPad|iPod/.test(navigator.userAgent);
}

// Chevron SVG — rotates when open
function Chevron({ isOpen }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{
        flexShrink: 0,
        transition: "transform 0.2s ease",
        transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
        color: "var(--vce-text-muted)",
      }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

// Tick SVG — shown on selected option
function Tick() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ flexShrink: 0, color: "var(--vce-accent, #0071e3)" }}
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function CustomDropdown({ id, value, onChange, options, placeholder }) {
  const [isOpen, setIsOpen] = useState(false);
  const [flipUp, setFlipUp] = useState(false);
  const triggerRef = useRef(null);
  const listRef = useRef(null);
  const containerRef = useRef(null);

  const selectedLabel =
    options.find((opt) => opt.value === value)?.label || "";

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Flip up if not enough space below
  function handleOpen() {
    if (!isOpen && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      setFlipUp(spaceBelow < 240);
    }
    setIsOpen((prev) => !prev);
  }

  function handleSelect(optionValue) {
    onChange(optionValue);
    setIsOpen(false);
  }

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      {/* Trigger button */}
      <button
        id={id}
        ref={triggerRef}
        type="button"
        onClick={handleOpen}
        className="vce-select"
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "8px",
          textAlign: "left",
          cursor: "pointer",
          background: "var(--vce-card-bg, #fff)",
          width: "100%",
        }}
      >
        <span
          style={{
            color: value ? "inherit" : "var(--vce-text-muted)",
            whiteSpace: "normal",
            wordBreak: "break-word",
            flex: 1,
          }}
        >
          {value ? selectedLabel : placeholder}
        </span>
        <Chevron isOpen={isOpen} />
      </button>

      {/* Floating options list */}
      {isOpen && (
        <ul
          ref={listRef}
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            ...(flipUp ? { bottom: "calc(100% + 6px)" } : { top: "calc(100% + 6px)" }),
            zIndex: 1000,
            background: "var(--vce-card-bg, #fff)",
            border: "1px solid var(--vce-border, #e0e0e0)",
            borderRadius: "12px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
            maxHeight: "220px",
            overflowY: "auto",
            padding: "6px",
            margin: 0,
            listStyle: "none",
          }}
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <li
                key={opt.value}
                className="vce-dropdown-option"
                onClick={() => handleSelect(opt.value)}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: "8px",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  background: isSelected
                    ? "var(--vce-accent-subtle, #f0f7ff)"
                    : "transparent",
                  fontWeight: isSelected ? "600" : "400",
                  color: "var(--vce-text, #1d1d1f)",
                  wordBreak: "break-word",
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected)
                    e.currentTarget.style.background =
                      "var(--vce-hover, #f5f5f7)";
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) e.currentTarget.style.background = "transparent";
                }}
              >
                <span style={{ flex: 1 }}>{opt.label}</span>
                {isSelected && <Tick />}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

// Main export — auto picks native or custom
export default function SmartSelect({ id, value, onChange, options, placeholder }) {
  const [useNative, setUseNative] = useState(true);

  useEffect(() => {
    setUseNative(isApplePlatform());
  }, []);

  if (useNative) {
    return (
      <select
        id={id}
        className="vce-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    );
  }

  return (
    <CustomDropdown
      id={id}
      value={value}
      onChange={onChange}
      options={options}
      placeholder={placeholder}
    />
  );
}