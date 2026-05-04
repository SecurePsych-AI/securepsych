import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface AuthState {
  token: string | null;
  username: string | null;
  setSession: (token: string, username: string) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      username: null,
      setSession: (token, username) => set({ token, username }),
      clear: () => set({ token: null, username: null }),
    }),
    {
      name: "securepsych:auth",
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);
