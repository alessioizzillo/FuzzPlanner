import { useEffect } from 'react'

export default function Error ({ error }) {
  useEffect(() => {
    console.log(error)
  }, [error])
  return (
    <div className='bg-rose-900 text-slate-200'>
      <div className='font-bold'>{error.code}</div>
      <div>{`${error.config.method} - ${error.config.baseURL}${error.config.url}`}</div>
      <div>{error.message}</div>
    </div>
  )
}
