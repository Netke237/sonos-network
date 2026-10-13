import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { InstallModal } from "../components/InstallModal";

describe("InstallModal", () => {
  it("does not render when isOpen is false", () => {
    const { container } = render(
      <InstallModal isOpen={false} onClose={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders QR code, download link, and instructions when open", () => {
    const handleClose = vi.fn();
    render(<InstallModal isOpen={true} onClose={handleClose} />);

    expect(
      screen.getByText("Install Sonos Network Companion")
    ).toBeInTheDocument();
    expect(
      screen.getByAltText("Companion App Installation QR Code")
    ).toHaveAttribute("src", expect.stringContaining("/api/companion/qr"));

    const downloadLink = screen.getByText("⬇️ Download APK Directly");
    expect(downloadLink).toHaveAttribute("href", expect.stringContaining("/api/companion/apk"));

    expect(
      screen.getByText("Local Wi-Fi & Firewalla VPN Ready")
    ).toBeInTheDocument();

    const closeBtn = screen.getByLabelText("Close install modal");
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
