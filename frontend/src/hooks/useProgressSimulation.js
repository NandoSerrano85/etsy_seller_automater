import { useState, useEffect, useCallback, useRef } from 'react';

export const useProgressSimulation = (actualProgress, isActive) => {
  const [simulatedProgress, setSimulatedProgress] = useState(actualProgress);
  const intervalRef = useRef(null);
  const lastActualProgressRef = useRef(actualProgress);

  const startSimulation = useCallback(() => {
    if (intervalRef.current) return;

    intervalRef.current = setInterval(() => {
      setSimulatedProgress(current => {
        const target = actualProgress.progressPercent || 0;
        const current_percent = current.progressPercent || 0;

        // If we're close to the target, slow down
        const diff = target - current_percent;
        if (Math.abs(diff) < 1) return current;

        // Simulate smooth progress increase
        const increment = Math.max(0.1, Math.min(0.5, diff * 0.1));
        const newPercent = Math.min(target, current_percent + increment);

        // Calculate estimated remaining time based on progress
        const remainingTime = actualProgress.remainingTime || 0;
        const adjustedRemainingTime = Math.max(0, remainingTime - 0.5);

        return {
          ...current,
          progressPercent: newPercent,
          remainingTime: adjustedRemainingTime,
          elapsedTime: (actualProgress.elapsedTime || 0) + 0.5,
        };
      });
    }, 500); // Update every 500ms for smooth animation
  }, [actualProgress]);

  const stopSimulation = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Update simulated progress when actual progress changes significantly
  useEffect(() => {
    const actualPercent = actualProgress.progressPercent || 0;
    const lastActualPercent = lastActualProgressRef.current.progressPercent || 0;

    // If actual progress jumped significantly, update simulated immediately
    if (Math.abs(actualPercent - lastActualPercent) > 2) {
      setSimulatedProgress(actualProgress);
    }

    lastActualProgressRef.current = actualProgress;

    // Start simulation if active and not at 100%
    if (isActive && actualPercent < 100) {
      startSimulation();
    } else {
      stopSimulation();
    }
  }, [actualProgress, isActive, startSimulation, stopSimulation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopSimulation();
  }, [stopSimulation]);

  // Return simulated progress when simulating, actual when complete
  const finalProgress = actualProgress.progressPercent >= 100 ? actualProgress : simulatedProgress;

  return {
    ...finalProgress,
    // Override with actual values for important fields
    step: actualProgress.step,
    totalSteps: actualProgress.totalSteps,
    message: actualProgress.message,
    estimatedTotalTime: actualProgress.estimatedTotalTime,
  };
};
