import { toTitleCase } from "../utils/titlecase";

export default function SubjectCard({ subject, grade, onGradeChange, onRemove }) {
  
  const fillPercentage = ((grade - 4) / (10 - 4)) * 100;
  const formattedName = toTitleCase(subject.name);

  return (
    <div className="vce-subject-card">
      <div className="vce-card-header">
        <div className="vce-subject-info">
          {/* Render the formatted name */}
          <h3 className="vce-subject-name">{formattedName}</h3>
          <span className="vce-subject-meta">
            {subject.code} • {subject.credits} Credits
          </span>
        </div>
        <button 
          onClick={() => onRemove(subject.name)}
          className="vce-remove-btn"
          aria-label="Remove subject"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      {/* Override class added to target centering */}
      <div className="vce-slider-container card-slider-override">
        <div className="vce-grade-labels">
          <span>Target Grade</span>
          <span className="vce-grade-highlight">{grade}</span>
        </div>
        
        <input 
          type="range" 
          min="4" 
          max="10" 
          step="1"
          value={grade}
          onChange={(e) => onGradeChange(subject.name, parseInt(e.target.value))}
          className="vce-slider"
          style={{
            background: `linear-gradient(to right, var(--vce-blue) ${fillPercentage}%, var(--vce-border) ${fillPercentage}%)`
          }}
        />
        
        <div className="vce-slider-ticks">
          <span>4 (Pass)</span>
          <span>10 (Max)</span>
        </div>
      </div>
    </div>
  );
}