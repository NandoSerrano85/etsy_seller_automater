'use client';

import { create } from 'zustand';

interface Mask {
  id: string;
  file: File | null;
  settings?: any;
}

interface MockupStore {
  masks: Mask[];
  addMask: (mask: Omit<Mask, 'id'>) => void;
}

export const useMockupStore = create<MockupStore>((set) => ({
  masks: [],

  addMask: (mask) =>
    set((state) => ({
      masks: [
        ...state.masks,
        {
          ...mask,
          id: crypto.randomUUID(),
        },
      ],
    })),
}));