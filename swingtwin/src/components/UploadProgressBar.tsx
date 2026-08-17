type Props = {
  slot: "face" | "dtl" | "tour";
  label: string;
  percent: number;
};

const SLOT_LABEL: Record<Props["slot"], string> = {
  face: "Face-on upload",
  dtl: "Down-the-line upload",
  tour: "Tour clip upload",
};

export function UploadProgressBar({ slot, label, percent }: Props) {
  const clamped = Math.min(100, Math.max(0, Math.round(percent)));

  return (
    <div className="twin-upload-progress" role="status" aria-live="polite">
      <div className="twin-upload-progress__head">
        <span>{SLOT_LABEL[slot]}</span>
        <strong>{clamped}%</strong>
      </div>
      <p>{label}</p>
      <div
        className="twin-upload-progress__track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        aria-label={label}
      >
        <div
          className="twin-upload-progress__fill"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
