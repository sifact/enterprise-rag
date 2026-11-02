import { CornerDownLeft } from "lucide-react";
import { useId } from "react";

export default function QuestionBox(props: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  max: number;
  busy: boolean;
  teamLabel: string;
}) {
  const { value, onChange, onSubmit, max, busy, teamLabel } = props;
  const id = useId();
  const tooLong = value.length > max;
  const empty = value.trim().length === 0;
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!busy && !empty && !tooLong) onSubmit();
      }}
    >
      <label htmlFor={id} className="mb-2 block font-cond text-[24px] font-semibold leading-tight">
        Ask the company documents
      </label>
      <p className="mb-3 text-muted">
        You'll only get answers from documents {teamLabel} is allowed to read.
      </p>
      <div className="rounded-md border border-rule bg-panel focus-within:border-focus">
        <textarea
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (!busy && !empty && !tooLong) onSubmit();
            }
          }}
          rows={2}
          placeholder="For example: how long is paid parental leave?"
          className="block w-full resize-none bg-transparent px-3.5 pt-3 text-[16px] leading-relaxed outline-none placeholder:text-muted"
          aria-describedby={`${id}-count`}
        />
        <div className="flex items-center justify-between gap-3 px-3.5 pb-2.5">
          <span id={`${id}-count`} className={`text-[13px] ${tooLong ? "text-[var(--r-hr)]" : "text-muted"}`}>
            {tooLong ? `Too long: shorten to ${max} characters` : `${value.length}/${max}`}
          </span>
          <button
            type="submit"
            disabled={busy || empty || tooLong}
            className="flex items-center gap-2 rounded-md bg-fg px-4 py-1.5 font-medium text-ink disabled:opacity-40"
          >
            {busy ? "Answering…" : "Ask"}
            {!busy && <CornerDownLeft size={15} aria-hidden />}
          </button>
        </div>
      </div>
    </form>
  );
}
