import { useEffect } from 'react'

export default function Error ({ error }) {
  useEffect(() => {
    console.log(error)
  }, [error])

  return (
    <div className='bg-rose-900 text-slate-200 p-2 rounded'>
      {error?.code && <div className='font-bold'>{error.code}</div>}

      {error?.config ? (
        <div>{`${error.config.method} - ${error.config.baseURL || ''}${error.config.url || ''}`}</div>
      ) : (
        <div>No request information available</div>
      )}

      {error?.message && <div>{error.message}</div>}
    </div>
  )
}
