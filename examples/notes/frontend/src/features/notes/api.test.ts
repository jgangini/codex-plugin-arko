import { afterEach, expect, it, vi } from "vitest";
import { createItem } from "./api";

afterEach(() => vi.unstubAllGlobals());

it("serializes priority through the generated typed HTTP consumer", async () => {
  const fetch = vi.fn(async (request: Request) => {
    expect(request.url).toBe(`${window.location.origin}/api/notes`);
    expect(request.headers.get("Authorization")).toBe("Bearer test-only");
    expect(await request.json()).toEqual({ title: "Task", priority: 5 });
    return new Response(JSON.stringify({ id: "1", title: "Task", priority: 5 }), {
      status: 201, headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetch);
  expect(await createItem("test-only", { title: "Task", priority: 5 })).toEqual({ id: "1", title: "Task", priority: 5 });
  expect(fetch).toHaveBeenCalledOnce();
});

it("rejects a server validation response", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: [] }), {
    status: 422, headers: { "Content-Type": "application/json" },
  })));
  await expect(createItem("test-only", { title: "Task", priority: 6 })).rejects.toThrow("Could not create item");
});
