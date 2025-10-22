import { useCallback } from 'react'
import { useState, useSetState } from '@/store'

export function useTheme () {
  const state = useState()
  return state.theme
}

export function useToggleTheme () {
  const setState = useSetState()
  return useCallback(() => {
    setState(prev => ({
      ...prev,
      theme: prev.theme === 'dark' ? 'light' : 'dark'
    }))
  }, [setState])
}
