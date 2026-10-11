import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AniCleanlinessMeter } from "../components/AniCleanlinessMeter";
import { LiveWaveformOscilloscope } from "../components/LiveWaveformOscilloscope";
import type { LiveRfSample } from "../types/topology";

describe("AniCleanlinessMeter Component (T8)", () => {
  it("renders Clean Air state for ANI levels 0-3", () => {
    render(<AniCleanlinessMeter aniLevel={2} />);
    expect(screen.getByText(/ANI 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Clean Air/i)).toBeInTheDocument();
  });

  it("renders Elevated Hash state for ANI levels 4-6", () => {
    render(<AniCleanlinessMeter aniLevel={5} />);
    expect(screen.getByText(/ANI 5/i)).toBeInTheDocument();
    expect(screen.getByText(/Elevated Hash/i)).toBeInTheDocument();
  });

  it("renders Severe Electronic EMI state for ANI levels 7-9", () => {
    render(<AniCleanlinessMeter aniLevel={9} />);
    expect(screen.getByText(/ANI 9/i)).toBeInTheDocument();
    expect(screen.getByText(/Severe Electronic EMI/i)).toBeInTheDocument();
  });

  it("renders N/A state when aniLevel is null or undefined", () => {
    render(<AniCleanlinessMeter aniLevel={null} />);
    expect(screen.getByText(/ANI N\/A/i)).toBeInTheDocument();
    expect(screen.getByText(/\(Wi-Fi\/Wired\)/i)).toBeInTheDocument();
  });

  it("opens the interactive Atheros receiver desensitization modal on click", () => {
    render(<AniCleanlinessMeter aniLevel={8} showExplanation={true} />);
    const learnBtn = screen.getByTitle(/What is OFDM ANI\?/i);
    fireEvent.click(learnBtn);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByText(/Understanding OFDM ANI \(Adaptive Noise Immunity\)/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/The Sequential Isolation Test:/i)).toBeInTheDocument();

    const closeBtn = screen.getByRole("button", { name: /Got it/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});

describe("LiveWaveformOscilloscope Component (T8)", () => {
  const mockSamples: LiveRfSample[] = [
    {
      rincon_uuid: "RINCON_542A1B63FE6E01400",
      zone_name: "Wohnzimmer_Bookshelf",
      ofdm_ani_level: 3,
      noise_floor_dbm: -105,
      phy_error_rate: 0.0,
      captured_at: new Date().toISOString(),
    },
    {
      rincon_uuid: "RINCON_542A1B63E23401400",
      zone_name: "Wohnzimmer_Buchregal",
      ofdm_ani_level: 8,
      noise_floor_dbm: -92,
      phy_error_rate: 168.4,
      captured_at: new Date().toISOString(),
    },
  ];

  it("renders rolling SVG waveform chart, peak KPIs, and speaker selection", () => {
    render(
      <LiveWaveformOscilloscope
        samples={mockSamples}
        isConnected={true}
        isPaused={false}
        roomFilter="all"
      />
    );

    expect(screen.getByText(/Live RF & PHY Error Oscilloscope/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Wohnzimmer_Buchregal/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/168.4/i).length).toBeGreaterThan(0);

    // Verify SVG chart elements exist
    expect(screen.getByTestId("oscilloscope-svg-canvas")).toBeInTheDocument();
  });

  it("renders interactive 3-step Sequential EMI Isolation Procedure guide", () => {
    render(
      <LiveWaveformOscilloscope
        samples={mockSamples}
        isConnected={true}
        isPaused={false}
        roomFilter="all"
      />
    );

    expect(
      screen.getByText(/Sequential EMI Isolation Procedure/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Step 1: Baseline/i)).toBeInTheDocument();
    expect(screen.getByText(/Step 2: Unplug Sequentially/i)).toBeInTheDocument();
    expect(screen.getByText(/Step 3: Watch for the Plunge/i)).toBeInTheDocument();
  });

  it("triggers pause/resume toggle callback", () => {
    const onTogglePause = vi.fn();
    render(
      <LiveWaveformOscilloscope
        samples={mockSamples}
        isConnected={true}
        isPaused={false}
        onTogglePause={onTogglePause}
      />
    );

    const pauseBtn = screen.getByRole("button", { name: /Pause/i });
    fireEvent.click(pauseBtn);
    expect(onTogglePause).toHaveBeenCalledTimes(1);
  });
});
