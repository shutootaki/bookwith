type SWRError = {
  status: number
} & Error

export async function fetcher<JSON = never>(
  input: RequestInfo,
  init?: RequestInit,
): Promise<JSON> {
  const res = await fetch(input, {
    ...init,
    headers: {
      ...init?.headers,
    },
  })

  if (!res.ok) {
    const error = await res.text()
    const err = new Error(error) as SWRError
    err.status = res.status
    throw err
  }

  return await res.json()
}
