export type GalleryQuery = {
  q: string;
  split: string;
  sort: "default" | "disagreement";
  page: number;
  pageSize: number;
};

function positiveInteger(value: string | null, fallback: number): number {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : fallback;
}

function gallerySort(value: string | null): GalleryQuery["sort"] {
  return value === "disagreement" ? value : "default";
}

export function parseGalleryQuery(search: string): GalleryQuery {
  const params = new URLSearchParams(search);
  return {
    q: params.get("q") ?? "",
    split: params.get("split") ?? "",
    sort: gallerySort(params.get("sort")),
    page: positiveInteger(params.get("page"), 1),
    pageSize: positiveInteger(params.get("page_size"), 30),
  };
}

export function withGalleryQuery(search: string, updates: Partial<GalleryQuery>): string {
  const params = new URLSearchParams(search);
  if (updates.q !== undefined) updates.q ? params.set("q", updates.q) : params.delete("q");
  if (updates.split !== undefined) updates.split ? params.set("split", updates.split) : params.delete("split");
  if (updates.sort !== undefined) updates.sort === "disagreement" ? params.set("sort", updates.sort) : params.delete("sort");
  if (updates.page !== undefined) updates.page > 1 ? params.set("page", String(updates.page)) : params.delete("page");
  if (updates.pageSize !== undefined) updates.pageSize !== 30 ? params.set("page_size", String(updates.pageSize)) : params.delete("page_size");
  const query = params.toString();
  return query ? `?${query}` : "";
}
