import useSWR from 'swr'

import { components } from '../../lib/openapi-schema/schema'
import { TEST_USER_ID } from '../../pages/_app'

import { fetcher } from './fetcher'

export function useLibrary() {
  const { data, error, mutate } = useSWR<
    components['schemas']['BooksResponse']
  >(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/books/user/${TEST_USER_ID}`,
    fetcher,
  )

  return {
    books: data?.books || [],
    error,
    mutate,
  }
}

export function useBookCovers() {
  const { data, mutate, isValidating } = useSWR<
    components['schemas']['CoversResponse']
  >(`${process.env.NEXT_PUBLIC_API_BASE_URL}/books/covers`, fetcher)

  return {
    covers: data?.covers || [],
    mutate,
    isCoverLoading: isValidating,
  }
}
