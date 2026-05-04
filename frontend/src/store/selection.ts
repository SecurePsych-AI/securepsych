import { create } from "zustand";
import type { UUID } from "@/types/api";

interface SelectionState {
  activeProjectId: UUID | null;
  setActiveProject: (id: UUID | null) => void;
}

export const useSelectionStore = create<SelectionState>((set) => ({
  activeProjectId: null,
  setActiveProject: (id) => set({ activeProjectId: id }),
}));
