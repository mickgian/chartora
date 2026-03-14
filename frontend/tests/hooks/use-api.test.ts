import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useApi } from "@/hooks/use-api";

describe("useApi", () => {
  it("starts in loading state", () => {
    const fetcher = vi.fn(() => new Promise<string>(() => {}));
    const { result } = renderHook(() => useApi(fetcher));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("returns data on success", async () => {
    const fetcher = vi.fn(() => Promise.resolve({ value: 42 }));
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ value: 42 });
    expect(result.current.error).toBeNull();
  });

  it("returns error on failure", async () => {
    const fetcher = vi.fn(() => Promise.reject(new Error("Network error")));
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toBeNull();
    expect(result.current.error?.message).toBe("Network error");
  });

  it("refetch triggers a new fetch", async () => {
    let callCount = 0;
    const fetcher = vi.fn(() => Promise.resolve({ count: ++callCount }));
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual({ count: 1 });

    result.current.refetch();

    await waitFor(() => expect(result.current.data).toEqual({ count: 2 }));
  });
});
