import { useState, useMemo, useEffect } from "react";
import {
  getFlattenedData,
  getPrograms,
  getDepartments,
  getSemesters,
} from "./utils/parser";
import SubjectCard from "./components/SubjectCard";
import { toTitleCase } from "./utils/titlecase";
import collegeLogo from "./assets/clg_logo.svg";
import { Analytics } from "@vercel/analytics/react";

export default function App() {
  const flatData = useMemo(() => getFlattenedData(), []);
  const availablePrograms = getPrograms();

  // State Management
  const [selectedProgram, setSelectedProgram] = useState("");
  const [selectedDept, setSelectedDept] = useState("");
  const [selectedSem, setSelectedSem] = useState("");
  const [activeSubjects, setActiveSubjects] = useState([]);
  const [grades, setGrades] = useState({});

  // Derived State for dropdown options
  const availableDepts = useMemo(
    () => getDepartments(selectedProgram),
    [selectedProgram],
  );
  const availableSems = useMemo(
    () => getSemesters(selectedProgram, selectedDept),
    [selectedProgram, selectedDept],
  );

  // Get current subjects BEFORE using it in hooks
  const currentSubjects = useMemo(() => {
    if (!selectedProgram || !selectedDept || !selectedSem) return [];
    return flatData.filter(
      (sub) =>
        sub.program === selectedProgram &&
        sub.dept === selectedDept &&
        sub.sem === parseInt(selectedSem),
    );
  }, [flatData, selectedProgram, selectedDept, selectedSem]);

  useEffect(() => {
    if (currentSubjects.length > 0) {
      const allNames = currentSubjects.map((sub) => sub.name);
      setActiveSubjects(allNames);

      const defaultGrades = {};
      allNames.forEach((name) => (defaultGrades[name] = 8)); // Default to 8
      setGrades(defaultGrades);
    } else {
      setActiveSubjects([]);
      setGrades({});
    }
  }, [currentSubjects]); // This only fires when the derived currentSubjects array changes

  // SGPA Mathematical Calculation O(N)
  const currentSGPA = useMemo(() => {
    if (activeSubjects.length === 0) return 0.0;

    let totalCredits = 0;
    let totalPoints = 0;

    activeSubjects.forEach((subjectName) => {
      // Find the subject details from the current pool
      const subjectDetails = currentSubjects.find(
        (sub) => sub.name === subjectName,
      );
      if (subjectDetails && subjectDetails.credits > 0) {
        const gradePoint = grades[subjectName] || 0;
        totalCredits += subjectDetails.credits;
        totalPoints += subjectDetails.credits * gradePoint;
      }
    });

    return totalCredits === 0 ? 0.0 : (totalPoints / totalCredits).toFixed(2);
  }, [activeSubjects, grades, currentSubjects]);

  // Handlers
  const handleProgramChange = (e) => {
    setSelectedProgram(e.target.value);
    setSelectedDept("");
    setSelectedSem("");
  };
  const handleDeptChange = (e) => {
    setSelectedDept(e.target.value);
    setSelectedSem("");
  };

  const handleSemChange = (e) => {
    setSelectedSem(e.target.value);
  };

  const handleRemoveSubject = (subjectName) => {
    setActiveSubjects((prev) => prev.filter((name) => name !== subjectName));
  };

  const handleRestoreSubject = (subjectName) => {
    setActiveSubjects((prev) => [...prev, subjectName]);
    if (grades[subjectName] === undefined) {
      setGrades((prev) => ({ ...prev, [subjectName]: 8 }));
    }
  };

  const handleGradeChange = (subjectName, newGrade) => {
    setGrades((prev) => ({ ...prev, [subjectName]: newGrade }));
  };

  // UI Split: Active vs Removed
  const activeList = currentSubjects.filter((sub) =>
    activeSubjects.includes(sub.name),
  );
  const removedList = currentSubjects.filter(
    (sub) => !activeSubjects.includes(sub.name),
  );
  return (
    <div
      style={{ maxWidth: "600px", margin: "0 auto", paddingBottom: "140px" }}
    >
      {/*Feedback Button */}
      <button
        className="vce-feedback-btn"
        onClick={() =>
          window.open(
            "https://docs.google.com/forms/d/e/1FAIpQLSdiOepAhPuaXfN_rN70XjeJb5DFtKKvM3HDeOee7bgL7LT-tw/viewform?usp=preview",
            "_blank",
          )
        }
        title="Send Feedback"
        aria-label="Send Feedback"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ transition: "stroke 0.2s ease" }}
        >
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
        </svg>
        <span>Feedback</span>
      </button>

      {/*Header Layout */}
      <header className="vce-header">
        <img src={collegeLogo} alt="College Logo" className="vce-header-logo" />
        <h1 className="vce-header-title">SGPA Calculator</h1>
      </header>

      <div className="vce-card">
        {/* Step 1: Program */}
        <div style={{ marginBottom: selectedProgram ? "16px" : "0" }}>
          <label htmlFor="program-select" className="vce-label">
            1. Program
          </label>
          <select
            id="program-select"
            className="vce-select"
            value={selectedProgram}
            onChange={handleProgramChange}
          >
            <option value="" disabled>
              Select program...
            </option>
            {availablePrograms.map((prog) => (
              <option key={prog} value={prog}>
                {prog}
              </option>
            ))}
          </select>
        </div>

        {/* Step 2: Department */}
        {selectedProgram && (
          <div
            style={{
              marginBottom: selectedDept ? "16px" : "0",
              animation: "fadeIn 0.3s ease",
            }}
          >
            <label htmlFor="dept-select" className="vce-label">
              2. Department
            </label>
            <select
              id="dept-select"
              className="vce-select"
              value={selectedDept}
              onChange={handleDeptChange}
            >
              <option value="" disabled>
                Select department...
              </option>
              {availableDepts.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Step 3: Semester */}
        {selectedDept && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>
            <label htmlFor="sem-select" className="vce-label">
              3. Semester
            </label>
            <select
              id="sem-select"
              className="vce-select"
              value={selectedSem}
              onChange={handleSemChange}
            >
              <option value="" disabled>
                Select semester...
              </option>
              {availableSems.map((sem) => (
                <option key={sem} value={sem}>
                  Semester {sem}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Step 4: Dynamic Subject Lists */}
      {selectedSem && currentSubjects.length > 0 && (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
          {/* NEW: Instructional Note */}
          <p className="vce-instruction-note">
            <span className="vce-text-danger">Remove any electives</span> or
            subjects you aren't taking this semester using the{" "}
            <span className="vce-text-danger">✕</span> button.
          </p>

          {/* Render Active Subject Cards */}
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            {activeList.map((sub) => (
              <SubjectCard
                key={`${sub.name}-${sub.code}`}
                subject={sub}
                grade={grades[sub.name] || 0}
                onGradeChange={handleGradeChange}
                onRemove={handleRemoveSubject}
              />
            ))}
          </div>

          {/* Render Removed Subjects Pool */}
          {removedList.length > 0 && (
            <div className="vce-removed-section">
              <h4 className="vce-removed-title">Removed Subjects</h4>
              <div className="vce-removed-list">
                {removedList.map((sub) => (
                  <div
                    key={`${sub.name}-${sub.code}`}
                    className="vce-removed-item"
                  >
                    <span className="vce-removed-name">
                      {toTitleCase(sub.name)}
                    </span>
                    <button
                      onClick={() => handleRestoreSubject(sub.name)}
                      className="vce-add-btn"
                    >
                      + Add
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* SGPA Sticky Footer */}
      {selectedSem && (
        <div className="vce-sticky-footer">
          <div className="vce-sgpa-container">
            <span className="vce-sgpa-label">SGPA</span>
            <span className="vce-sgpa-value">{currentSGPA}</span>
          </div>
        </div>
      )}

      <Analytics />
    </div>
  );
}
