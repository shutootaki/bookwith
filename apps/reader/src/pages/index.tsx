import Head from 'next/head'
import { useRouter } from 'next/router'
import React, { useEffect, useState } from 'react'

import { ReaderGridView } from '../components'
import { Library } from '../components/Library'
import { useDisablePinchZooming } from '../hooks'
import {
  RemoteImportError,
  fetchBook,
  handleFiles,
  isAllowedRemoteImportUrl,
} from '../lib/apiHandler/importHandlers'
import { reader, useReaderSnapshot } from '../models'

const SOURCE = 'src'

export default function Index() {
  const { focusedTab } = useReaderSnapshot()
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  useDisablePinchZooming()

  useEffect(() => {
    // CR-7: クエリ `?src=` で渡された URL を確認なしに自動 fetch しない。
    let src = router.query[SOURCE]
    if (!src) return
    if (!Array.isArray(src)) src = [src]

    const allowed = src.filter(isAllowedRemoteImportUrl)
    const blocked = src.filter((u) => !isAllowedRemoteImportUrl(u))

    if (blocked.length > 0) {
      console.warn('Blocked untrusted remote import URLs:', blocked)
      window.alert(
        'Some import URLs are not on the trusted host list and were ignored.',
      )
    }
    if (allowed.length === 0) return

    const confirmMessage = `Import EPUB(s) from the following URL(s)?\n\n${allowed.join('\n')}`
    // window.confirm は同期確認。ユーザーが明示的に許可した URL のみ取り込む。
    if (!window.confirm(confirmMessage)) return

    setLoading(true)
    Promise.all(
      allowed.map((s) =>
        fetchBook(s)
          .then((b) => {
            if (b) reader.addTab(b)
          })
          .catch((err) => {
            if (err instanceof RemoteImportError) {
              window.alert(err.message)
            } else {
              console.error(err)
            }
          }),
      ),
    ).finally(() => setLoading(false))
  }, [router.query])

  useEffect(() => {
    if ('launchQueue' in window && 'LaunchParams' in window) {
      window.launchQueue.setConsumer((params) => {
        if (params.files.length) {
          Promise.all(params.files.map((f) => f.getFile()))
            .then((files) => handleFiles(files))
            .then((result) => {
              if (result && 'newBooks' in result) {
                result.newBooks.forEach((b) => reader.addTab(b))
              }
            })
        }
      })
    }
  }, [])

  useEffect(() => {
    router.beforePopState(({ url }) => {
      if (url === '/') {
        reader.clear()
      }
      return true
    })
  }, [router])

  return (
    <>
      <Head>
        {/* Disable pinch zooming */}
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no"
        />
        <title>{focusedTab?.title ?? 'Bookwith'}</title>
      </Head>
      <ReaderGridView />
      {loading || <Library />}
    </>
  )
}
