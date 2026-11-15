import { useState } from "react";

interface Props {
  id: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  autoComplete?: string;
}

/** A password <input> with a show/hide toggle, used by both login and
 * register (register needs two - password and confirm password - so this
 * is a component rather than copy-pasted into each form). */
export default function PasswordInput({
  id,
  value,
  onChange,
  placeholder,
  disabled,
  required,
  autoComplete,
}: Props) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="form-input-wrapper">
      <input
        id={id}
        type={visible ? "text" : "password"}
        className="form-input"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        required={required}
        autoComplete={autoComplete}
      />
      <button
        type="button"
        className="form-input-toggle"
        onClick={() => setVisible((v) => !v)}
        disabled={disabled}
        // Not in the tab order - it's a convenience toggle next to the
        // field, not a step in filling out the form.
        tabIndex={-1}
      >
        {visible ? "Hide" : "Show"}
      </button>
    </div>
  );
}
