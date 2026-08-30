import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { createFinding } from "../../api/client";
import type { Collection } from "../../api/types";

type SaveFindingFormProps = { sampleId: string; collections: Collection[] };

function tagsFromInput(value: string) {
  return [...new Set(value.split(",").map(tag => tag.trim()).filter(Boolean))].slice(0, 8);
}

export function SaveFindingForm({ sampleId, collections }: SaveFindingFormProps) {
  const [collectionId, setCollectionId] = useState("");
  const [tags, setTags] = useState("");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const selected = collections.find(collection => collection.id === Number(collectionId));
    if (!selected) return setStatus("Choose a collection before saving.");
    setIsSaving(true);
    setStatus("");
    try {
      await createFinding(selected.id, { sample_id: sampleId, tags: tagsFromInput(tags), note });
      setStatus(`Saved to ${selected.name}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not save finding.");
    } finally {
      setIsSaving(false);
    }
  }

  return <section className="save-finding" aria-labelledby="save-finding-title">
    <p className="eyebrow">Keep a local research note</p><h2 id="save-finding-title">Save this finding</h2>
    <form onSubmit={submit}>
      <label>Collection<select value={collectionId} onChange={event => setCollectionId(event.target.value)} required><option value="">Choose a collection</option>{collections.map(collection => <option key={collection.id} value={collection.id}>{collection.name}</option>)}</select></label>
      <label>Tags<input value={tags} onChange={event => setTags(event.target.value)} placeholder="action, ambiguity" /></label>
      <label>Note<textarea value={note} onChange={event => setNote(event.target.value)} rows={3} /></label>
      <button type="submit" disabled={isSaving || collections.length === 0}>{isSaving ? "Saving…" : "Save finding"}</button>
    </form>
    {collections.length === 0 && <p className="status">Create a collection before saving findings.</p>}
    <p className="save-status" role="status" aria-live="polite">{status}{status.startsWith("Saved to") && <> <Link to="/collections">Collections</Link></>}</p>
  </section>;
}
