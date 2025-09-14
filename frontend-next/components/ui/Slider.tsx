'use client';

import React from 'react';
import clsx from 'clsx';

interface SliderProps {
  value?: number[];
  defaultValue?: number[];
  min?: number;
  max?: number;
  step?: number;
  onValueChange?: (value: number[]) => void;
  className?: string;
  'aria-label'?: string;
}

export function Slider({
  value,
  defaultValue = [0],
  min = 0,
  max = 100,
  step = 1,
  onValueChange,
  className,
  'aria-label': ariaLabel,
  ...props
}: SliderProps) {
  const [internalValue, setInternalValue] = React.useState(value || defaultValue);

  const currentValue = value || internalValue;
  const percentage = ((currentValue[0] - min) / (max - min)) * 100;

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = [Number(event.target.value)];
    if (!value) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };

  return (
    <div className={clsx('relative flex items-center w-full', className)}>
      <div className="relative flex-1 h-2">
        <div className="absolute inset-0 bg-gray-200 rounded-full" />
        <div
          className="absolute inset-y-0 left-0 bg-primary rounded-full"
          style={{ width: `${percentage}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={currentValue[0]}
          onChange={handleChange}
          className="absolute inset-0 w-full h-2 opacity-0 cursor-pointer"
          aria-label={ariaLabel}
          {...props}
        />
        <div
          className="absolute w-4 h-4 bg-white border-2 border-primary rounded-full shadow-sm -mt-1 cursor-pointer"
          style={{ left: `calc(${percentage}% - 8px)` }}
        />
      </div>
    </div>
  );
}