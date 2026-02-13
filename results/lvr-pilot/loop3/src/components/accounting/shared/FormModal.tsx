/**
 * FormModal — Reusable form modal for create/edit operations.
 *
 * Used by 10+ accounting pages for creating and editing entities
 * (invoices, bills, expenses, journal entries, chart of accounts, fixed assets, etc.).
 *
 * Features:
 *   - Declarative field definitions (no manual form JSX)
 *   - Built-in validation (required fields, format rules)
 *   - Loading state on submit
 *   - Error display (field-level and form-level)
 *   - Controlled via isOpen/onClose (no internal open state)
 */

import React, { useState, useEffect, useCallback, type FormEvent } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle, Loader2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FormFieldType = 'text' | 'number' | 'date' | 'select' | 'textarea' | 'email' | 'tel';

export interface SelectOption {
  /** The stored value */
  value: string;
  /** The display label */
  label: string;
}

export interface FormFieldConfig {
  /** Unique field name (used as the key in form values) */
  name: string;
  /** Display label */
  label: string;
  /** Field type */
  type: FormFieldType;
  /** Whether the field is required. Default: false */
  required?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Options for 'select' type fields */
  options?: SelectOption[];
  /** Default value */
  defaultValue?: any;
  /** Whether the field is disabled */
  disabled?: boolean;
  /** Help text shown below the field */
  helpText?: string;
  /** Minimum value (for 'number' type) */
  min?: number;
  /** Maximum value (for 'number' type) */
  max?: number;
  /** Step value (for 'number' type) */
  step?: number;
  /** Number of rows (for 'textarea' type). Default: 3 */
  rows?: number;
  /** Custom validation function. Return an error message string, or undefined if valid. */
  validate?: (value: any, allValues: Record<string, any>) => string | undefined;
  /** Width class (e.g., 'col-span-2' for full width in a 2-column grid) */
  colSpan?: string;
}

export interface FormModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback to close the modal */
  onClose: () => void;
  /** Modal title */
  title: string;
  /** Optional description below the title */
  description?: string;
  /** Field definitions */
  fields: FormFieldConfig[];
  /** Initial values (for edit mode) */
  initialValues?: Record<string, any>;
  /** Submit handler. Must return a promise that resolves on success. */
  onSubmit: (values: Record<string, any>) => Promise<void>;
  /** Whether a submission is in progress */
  isSubmitting?: boolean;
  /** Submit button label. Default: 'Save' */
  submitLabel?: string;
  /** Cancel button label. Default: 'Cancel' */
  cancelLabel?: string;
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateField(
  field: FormFieldConfig,
  value: any,
  allValues: Record<string, any>
): string | undefined {
  // Required check
  if (field.required) {
    if (value === undefined || value === null || value === '') {
      return `${field.label} is required`;
    }
  }

  // Skip further validation if empty and not required
  if (value === undefined || value === null || value === '') {
    return undefined;
  }

  // Number range check
  if (field.type === 'number') {
    const num = Number(value);
    if (isNaN(num)) {
      return `${field.label} must be a valid number`;
    }
    if (field.min !== undefined && num < field.min) {
      return `${field.label} must be at least ${field.min}`;
    }
    if (field.max !== undefined && num > field.max) {
      return `${field.label} must be at most ${field.max}`;
    }
  }

  // Email format check
  if (field.type === 'email' && typeof value === 'string') {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Please enter a valid email address';
    }
  }

  // Custom validation
  if (field.validate) {
    return field.validate(value, allValues);
  }

  return undefined;
}

function validateAllFields(
  fields: FormFieldConfig[],
  values: Record<string, any>
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const field of fields) {
    const error = validateField(field, values[field.name], values);
    if (error) {
      errors[field.name] = error;
    }
  }
  return errors;
}

// ---------------------------------------------------------------------------
// Field Renderers
// ---------------------------------------------------------------------------

function renderField(
  field: FormFieldConfig,
  value: any,
  error: string | undefined,
  onChange: (name: string, value: any) => void
) {
  const fieldId = `form-field-${field.name}`;
  const hasError = !!error;

  const fieldElement = (() => {
    switch (field.type) {
      case 'textarea':
        return (
          <Textarea
            id={fieldId}
            value={value ?? ''}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            rows={field.rows ?? 3}
            className={hasError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          />
        );

      case 'select':
        return (
          <Select
            value={value ?? ''}
            onValueChange={(v) => onChange(field.name, v)}
            disabled={field.disabled}
          >
            <SelectTrigger
              id={fieldId}
              className={hasError ? 'border-red-500 focus:ring-red-500' : ''}
            >
              <SelectValue placeholder={field.placeholder ?? 'Select...'} />
            </SelectTrigger>
            <SelectContent>
              {(field.options ?? []).map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'number':
        return (
          <Input
            id={fieldId}
            type="number"
            value={value ?? ''}
            onChange={(e) => onChange(field.name, e.target.value === '' ? '' : Number(e.target.value))}
            placeholder={field.placeholder}
            disabled={field.disabled}
            min={field.min}
            max={field.max}
            step={field.step}
            className={hasError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          />
        );

      case 'date':
        return (
          <Input
            id={fieldId}
            type="date"
            value={value ?? ''}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            className={hasError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          />
        );

      case 'email':
        return (
          <Input
            id={fieldId}
            type="email"
            value={value ?? ''}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            className={hasError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          />
        );

      case 'tel':
        return (
          <Input
            id={fieldId}
            type="tel"
            value={value ?? ''}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            className={hasError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          />
        );

      case 'text':
      default:
        return (
          <Input
            id={fieldId}
            type="text"
            value={value ?? ''}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={field.disabled}
            className={hasError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          />
        );
    }
  })();

  return (
    <div key={field.name} className={`space-y-2 ${field.colSpan ?? ''}`}>
      <Label htmlFor={fieldId} className={hasError ? 'text-red-600' : ''}>
        {field.label}
        {field.required && <span className="text-red-500 ml-0.5">*</span>}
      </Label>
      {fieldElement}
      {field.helpText && !hasError && (
        <p className="text-xs text-muted-foreground">{field.helpText}</p>
      )}
      {hasError && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// FormModal Component
// ---------------------------------------------------------------------------

export function FormModal({
  isOpen,
  onClose,
  title,
  description,
  fields,
  initialValues,
  onSubmit,
  isSubmitting: externalSubmitting,
  submitLabel = 'Save',
  cancelLabel = 'Cancel',
}: FormModalProps) {
  const [values, setValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [internalSubmitting, setInternalSubmitting] = useState(false);

  const isSubmitting = externalSubmitting ?? internalSubmitting;

  // Reset form when modal opens or initialValues change
  useEffect(() => {
    if (isOpen) {
      const defaultValues: Record<string, any> = {};
      for (const field of fields) {
        defaultValues[field.name] =
          initialValues?.[field.name] ?? field.defaultValue ?? '';
      }
      setValues(defaultValues);
      setErrors({});
      setFormError(null);
    }
  }, [isOpen, initialValues, fields]);

  const handleChange = useCallback((name: string, value: any) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    // Clear field error on change
    setErrors((prev) => {
      if (prev[name]) {
        const next = { ...prev };
        delete next[name];
        return next;
      }
      return prev;
    });
    setFormError(null);
  }, []);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();

      // Validate all fields
      const validationErrors = validateAllFields(fields, values);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        return;
      }

      setInternalSubmitting(true);
      setFormError(null);

      try {
        await onSubmit(values);
        // If onSubmit resolves successfully, close the modal
        onClose();
      } catch (err: any) {
        const message =
          err?.message ?? 'An unexpected error occurred. Please try again.';
        setFormError(message);
      } finally {
        setInternalSubmitting(false);
      }
    },
    [fields, values, onSubmit, onClose]
  );

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isSubmitting && onClose()}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            {description && <DialogDescription>{description}</DialogDescription>}
          </DialogHeader>

          {/* Form-level error */}
          {formError && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2 mt-4">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {formError}
            </div>
          )}

          {/* Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-4">
            {fields.map((field) =>
              renderField(field, values[field.name], errors[field.name], handleChange)
            )}
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              {cancelLabel}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default FormModal;
