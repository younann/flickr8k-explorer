import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createCollection, deleteFinding, getCollections, getFindings } from "../../api/client";
import type { Collection, Finding } from "../../api/types";
import { Feedback } from "../../components/Feedback";

type CollectionWithFindings = Collection & { findings: Finding[] };

export function CollectionsPage() {
  const [collections, setCollections] = useState<CollectionWithFindings[] | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [status, setStatus] = useState("");
  const [collectionName, setCollectionName] = useState("");

  useEffect(() => {
    let active = true;
    getCollections()
      .then(async ({ items }) => Promise.all(items.map(async collection => ({ ...collection, findings: (await getFindings(collection.id)).items }))))
      .then(items => { if (active) setCollections(items); })
      .catch(error => { if (active) setError(error); });
    return () => { active = false; };
  }, []);

  async function removeFinding(collectionId: number, findingId: number) {
    setStatus("");
    try {
      await deleteFinding(findingId);
      setCollections(current => current?.map(collection => collection.id === collectionId
        ? { ...collection, finding_count: Math.max(0, collection.finding_count - 1), findings: collection.findings.filter(finding => finding.id !== findingId) }
        : collection,
      ) ?? null);
      setStatus("Finding deleted");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not delete finding.");
    }
  }

  async function createLocalCollection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("");
    try {
      const collection = await createCollection({ name: collectionName.trim() });
      setCollections(current => [{ ...collection, findings: [] }, ...(current ?? [])]);
      setCollectionName("");
      setStatus(`Created ${collection.name}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not create collection.");
    }
  }

  if (error) return <main><Feedback error={error} /></main>;
  return <main className="collections-page">
    <div className="page-title"><p className="eyebrow">Local research notes</p><h1>Collections</h1><p>Keep evidence-backed findings on this device, then export a collection for the next stage of analysis.</p></div>
    {collections === null && <p className="status">Loading collections…</p>}
    <form className="collection-create" onSubmit={createLocalCollection}><label>New collection name<input value={collectionName} onChange={event => setCollectionName(event.target.value)} required maxLength={80} /></label><button type="submit">Create collection</button></form>
    <p className="save-status" role="status" aria-live="polite">{status}</p>
    {collections?.map(collection => <section className="collection-card" key={collection.id} aria-labelledby={`collection-${collection.id}`}>
      <div className="collection-heading"><div><p className="eyebrow">{collection.finding_count} saved findings</p><h2 id={`collection-${collection.id}`}>{collection.name}</h2></div><div className="collection-actions"><a href={`/api/collections/${collection.id}/export?format=csv`}>Export CSV</a><a href={`/api/collections/${collection.id}/export?format=json`}>Export JSON</a></div></div>
      {collection.findings.length === 0 && <p className="status">No findings have been saved in this collection.</p>}
      <ul className="finding-list">{collection.findings.map(finding => <li key={finding.id}>
        <div><Link to={`/samples/${finding.sample_id}`}>{finding.sample_id}</Link>{finding.tags.length > 0 && <p className="tags">{finding.tags.map(tag => <span key={tag}>{tag}</span>)}</p>}<p>{finding.note || "No note added."}</p></div>
        <button type="button" onClick={() => removeFinding(collection.id, finding.id)} aria-label={`Delete finding ${finding.id}`}>Delete</button>
      </li>)}</ul>
    </section>)}
    {collections?.length === 0 && <p className="status">No collections are available yet.</p>}
  </main>;
}
