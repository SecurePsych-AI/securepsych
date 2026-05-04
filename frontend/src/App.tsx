import { AppRouter } from "@/router";
import { Toaster } from "@/components/ui/toaster";

export default function App() {
  return (
    <>
      <AppRouter />
      <Toaster />
    </>
  );
}
