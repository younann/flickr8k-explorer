import { ApiError } from "../api/client";

type FeedbackProps = {
  error: Error;
};

export function Feedback({ error }: FeedbackProps) {
  const message = error instanceof ApiError && error.status === 409
    ? "Import the dataset before browsing."
    : error.message;

  return <p className="notice" role="alert">{message}</p>;
}
