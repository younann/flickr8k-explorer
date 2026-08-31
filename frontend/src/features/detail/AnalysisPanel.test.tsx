import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { AnalysisPanel } from "./AnalysisPanel";

const analysis = {
  sample_id: "fixture-dog-1",
  disagreement_score: 82,
  token_disagreement: 0.67,
  vocabulary_diversity: 0.71,
  mean_caption_length: 5.5,
  caption_length_spread: 1.2,
  differing_tokens: ["runs", "plays"],
};

test("keeps each evidence caption in one inline text column", () => {
  render(<AnalysisPanel
    analysis={analysis}
    captions={["A dog runs outside.", "A dog plays outside."]}
    neighbors={[]}
  />);

  for (const row of screen.getAllByRole("listitem")) {
    expect(row.querySelectorAll(":scope > .evidence-caption-text")).toHaveLength(1);
    expect(row.querySelectorAll(":scope > mark")).toHaveLength(0);
  }
});
