import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { StoreProvider, useState } from '@/store'
import PollingDebugPanel from '@/components/PollingDebugPanel'
import '@/styles/globals.css'
import 'reactflow/dist/style.css'

function ThemeWrapper ({ children }) {
  const state = useState()

  React.useEffect(() => {
    const root = document.documentElement
    if (state.theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [state.theme])

  return children
}

export default function App ({ Component, pageProps }) {
  const [queryClient] = React.useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 20
      }
    }
  }))
  return (
    <QueryClientProvider client={queryClient}>
      <StoreProvider>
        <ThemeWrapper>
          <Component {...pageProps} />
          {/* <PollingDebugPanel /> */}
        </ThemeWrapper>
      </StoreProvider>
    </QueryClientProvider>
  )
}
