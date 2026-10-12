import "@testing-library/jest-dom";

if (typeof window !== "undefined" && !window.PointerEvent) {
  (window as unknown as { PointerEvent: unknown }).PointerEvent = window.MouseEvent;
}
