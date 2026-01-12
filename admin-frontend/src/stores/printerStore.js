import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const usePrinterStore = create(
  persist(
    (set, get) => ({
      // Printer state
      printers: [],
      defaultPrinter: null,
      printersLoading: false,
      printersError: null,

      // Printer management actions
      setPrinters: printers =>
        set({
          printers,
          printersError: null,
        }),

      addPrinter: printer =>
        set(state => ({
          printers: [...state.printers, printer],
          printersError: null,
        })),

      updatePrinter: updatedPrinter =>
        set(state => ({
          printers: state.printers.map(printer => (printer.id === updatedPrinter.id ? updatedPrinter : printer)),
          defaultPrinter: state.defaultPrinter?.id === updatedPrinter.id ? updatedPrinter : state.defaultPrinter,
          printersError: null,
        })),

      removePrinter: printerId =>
        set(state => ({
          printers: state.printers.filter(printer => printer.id !== printerId),
          defaultPrinter: state.defaultPrinter?.id === printerId ? null : state.defaultPrinter,
          printersError: null,
        })),

      setDefaultPrinter: printer =>
        set({
          defaultPrinter: printer,
          printersError: null,
        }),

      setPrintersLoading: loading => set({ printersLoading: loading }),

      setPrintersError: error => set({ printersError: error }),

      clearPrintersData: () =>
        set({
          printers: [],
          defaultPrinter: null,
          printersError: null,
        }),

      // Helper methods
      getPrinterById: printerId => {
        const { printers } = get();
        return printers.find(printer => printer.id === printerId);
      },

      getActivePrinters: () => {
        const { printers } = get();
        return printers.filter(printer => printer.is_active);
      },

      getPrintersByType: templateId => {
        const { printers } = get();
        return printers.filter(printer => printer.is_active && printer.supported_template_ids.includes(templateId));
      },

      // Get printers that can handle specific dimensions
      getPrintersForDimensions: (widthInches, heightInches) => {
        const { printers } = get();
        return printers.filter(
          printer =>
            printer.is_active && printer.max_width_inches >= widthInches && printer.max_height_inches >= heightInches
        );
      },

      // Debug info
      getDebugInfo: () => {
        const state = get();
        return {
          printerCount: state.printers.length,
          activePrinterCount: state.getActivePrinters().length,
          defaultPrinter: {
            id: state.defaultPrinter?.id,
            name: state.defaultPrinter?.name,
            type: state.defaultPrinter?.printer_type,
          },
          loading: state.printersLoading,
          error: state.printersError,
        };
      },
    }),
    {
      name: 'printer-store',
      partialize: state => ({
        printers: state.printers,
        defaultPrinter: state.defaultPrinter,
      }),
    }
  )
);

export default usePrinterStore;
