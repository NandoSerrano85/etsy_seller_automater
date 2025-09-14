'use client';

import { useState } from 'react';

interface MaskData {
  id: string;
  name: string;
  file: File;
  adjustments: {
    scale: number;
    rotation: number;
    opacity: number;
  };
  createdAt: Date;
}

export function useMockupStore() {
  const [masks, setMasks] = useState<MaskData[]>([]);

  const addMask = (maskData: Omit<MaskData, 'id' | 'createdAt'>) => {
    const newMask: MaskData = {
      ...maskData,
      id: Date.now().toString(),
      createdAt: new Date(),
    };
    setMasks(prev => [...prev, newMask]);
    return newMask;
  };

  const removeMask = (id: string) => {
    setMasks(prev => prev.filter(mask => mask.id !== id));
  };

  const updateMask = (id: string, updates: Partial<MaskData>) => {
    setMasks(prev => prev.map(mask =>
      mask.id === id ? { ...mask, ...updates } : mask
    ));
  };

  return {
    masks,
    addMask,
    removeMask,
    updateMask,
  };
}