import {
  Eye,
  EyeOff,
} from 'lucide-react';

import {
  useState,
  type InputHTMLAttributes,
} from 'react';


// =====================================================
// PASSWORD INPUT PROPS
// =====================================================

type PasswordInputProps =
  Omit<
    InputHTMLAttributes<HTMLInputElement>,
    'type'
  >;


// =====================================================
// PASSWORD INPUT
// =====================================================

/**
 * Reusable password field with an integrated visibility
 * toggle.
 *
 * The toggle is positioned inside the field rather than
 * beside it, keeping authentication forms compact and
 * visually consistent.
 *
 * Accessibility:
 * - the toggle is a real button;
 * - aria-label communicates the current action;
 * - pressing the toggle does not submit the form;
 * - password-manager/autocomplete behaviour remains
 *   controlled by the parent component.
 */
export function PasswordInput(
  props: PasswordInputProps,
) {
  const [
    visible,
    setVisible,
  ] =
    useState(false);

  return (
    <div className="password-input-shell">
      <input
        {...props}
        type={
          visible
            ? 'text'
            : 'password'
        }
        className={
          [
            'password-input-field',
            props.className,
          ]
            .filter(Boolean)
            .join(' ')
        }
      />

      <button
        type="button"
        className="password-visibility-toggle"
        aria-label={
          visible
            ? 'Hide password'
            : 'Show password'
        }
        title={
          visible
            ? 'Hide password'
            : 'Show password'
        }
        onClick={
          () =>
            setVisible(
              (current) =>
                !current,
            )
        }
      >
        {
          visible
            ? (
              <EyeOff size={17} />
            )
            : (
              <Eye size={17} />
            )
        }
      </button>
    </div>
  );
}
