import { client } from "../../shared/client";
import type { paths } from "../../shared/api.generated";

export type CreateItem = paths["/api/notes"]["post"]["requestBody"]["content"]["application/json"];

export async function createItem(token: string, body: CreateItem) {
  const { data, error } = await client(token).POST("/api/notes", { body });
  if (error || !data) throw new Error("Could not create item");
  return data;
}
