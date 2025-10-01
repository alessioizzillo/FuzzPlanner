import { useState, useEffect } from 'react'
import { useGetPcaps, useRemovePcap, useAnalyzePcap, useStopPcapReplay } from '@/hooks/queries'
import { useOptimizedPcapReplayProgress } from '@/hooks/useOptimizedPolling'
import {
  useSelectedPcap,
  useSetSelectedPcap,
  useResetSelectedPcap
} from '@/hooks/store/selectedPcap'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'

import Icon from '@/components/Icon'
import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function PcapPicker () {
  const firmwareId = useSelectedFirmware()
  const brandId = useSelectedBrand()
  const selectedPcap = useSelectedPcap()
  const setSelectedPcap = useSetSelectedPcap()
  const resetSelectedPcap = useResetSelectedPcap()
  const [showSuccessMessage, setShowSuccessMessage] = useState(false)
  const [isAnalysisInitiated, setIsAnalysisInitiated] = useState(false)
  const [isStopInitiated, setIsStopInitiated] = useState(false)

  const { isLoading, isError, error, data: pcaps, refetch } = useGetPcaps(brandId, firmwareId)
  const removePcapMutation = useRemovePcap()
  const analyzePcapMutation = useAnalyzePcap()
  const stopPcapReplayMutation = useStopPcapReplay()

  const { data: progressData, isLoading: isProgressLoading, refresh: refreshProgress } = useOptimizedPcapReplayProgress(
    brandId,
    firmwareId,
    selectedPcap
  )

  const isAnalysisRunning = progressData &&
    progressData.status !== 'not_running' &&
    progressData.phase !== 'completed' &&
    progressData.phase !== 'error'

  const isButtonDisabled = analyzePcapMutation.isPending || isAnalysisRunning || isAnalysisInitiated || analyzePcapMutation.isLoading

  useEffect(() => {
    setShowSuccessMessage(false)
    setIsAnalysisInitiated(false)
    setIsStopInitiated(false)
  }, [selectedPcap])

  useEffect(() => {
    if (progressData && (progressData.phase === 'completed' || progressData.phase === 'error')) {
      const timer = setTimeout(() => {
        setIsAnalysisInitiated(false)
        setShowSuccessMessage(false)
      }, 3000)
      return () => clearTimeout(timer)
    } else if (progressData === null && isAnalysisInitiated && !analyzePcapMutation.isPending) {
      const timer = setTimeout(() => {
        setIsAnalysisInitiated(false)
        setShowSuccessMessage(false)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [progressData, isAnalysisInitiated, analyzePcapMutation.isPending])

  useEffect(() => {
    if (isAnalysisRunning && !analyzePcapMutation.isPending) {
      setIsAnalysisInitiated(true)
    }
  }, [isAnalysisRunning, analyzePcapMutation.isPending])

  useEffect(() => {
    if (!isProgressLoading && !analyzePcapMutation.isPending && !isAnalysisRunning && isAnalysisInitiated) {
      const timer = setTimeout(() => {
        setIsAnalysisInitiated(false)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [isProgressLoading, analyzePcapMutation.isPending, isAnalysisRunning, isAnalysisInitiated])

  useEffect(() => {
    if (!isAnalysisRunning && isStopInitiated) {
      const timer = setTimeout(() => {
        setIsStopInitiated(false)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [isAnalysisRunning, isStopInitiated])

  if (isLoading) return <Spinner />
  if (isError) return <Error error={error} />

  const handleSelect = pcapName => {
    setSelectedPcap(pcapName)
  }

  const handleRemoveSelectedPcap = async () => {
    try {
      await removePcapMutation.mutateAsync({
        brandId,
        firmwareId,
        pcapName: selectedPcap
      })
      resetSelectedPcap()
      refetch()
    } catch (error) {
      console.error('Failed to remove PCAP:', error)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedPcap || isButtonDisabled) return

    setIsAnalysisInitiated(true)
    setShowSuccessMessage(false)

    try {
      const response = await analyzePcapMutation.mutateAsync({
        brandId,
        firmwareId,
        pcapName: selectedPcap
      })

      if (response.status === 'success') {
        setShowSuccessMessage(true)
        refreshProgress()
      } else {
        setIsAnalysisInitiated(false)
        setShowSuccessMessage(false)
      }
    } catch (error) {
      console.error('Failed to analyze PCAP:', error)
      setShowSuccessMessage(false)
      setIsAnalysisInitiated(false)
    }
  }

  const handleStopAnalysis = async () => {
    if (!selectedPcap || !isAnalysisRunning || isStopInitiated) return

    setIsStopInitiated(true)

    try {
      await stopPcapReplayMutation.mutateAsync({
        brandId,
        firmwareId,
        pcapName: selectedPcap
      })
      setIsAnalysisInitiated(false)
      setShowSuccessMessage(false)
    } catch (error) {
      console.error('Failed to stop PCAP replay:', error)
      setIsStopInitiated(false)
    }
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex items-center gap-4">
        {/* PCAP Picker and Remove Button grouped together */}
        <div className="flex items-center">
          <Picker
            items={pcaps.map(p => ({ id: p, label: p }))}
            selected={selectedPcap}
            setSelected={handleSelect}
            resetSelected={resetSelectedPcap}
            placeholder="Select a PCAP..."
            onOpen={() => {
              refetch()
            }}
          />

          {/* Remove Button - next to picker */}
          {selectedPcap && (
            <button
              onClick={handleRemoveSelectedPcap}
              className="-ml-5 rounded transition-colors text-red-500 hover:text-red-700 hover:bg-red-50 disabled:text-gray-400 disabled:cursor-not-allowed"
              disabled={removePcapMutation.isPending}
              title="Remove selected PCAP"
            >
              <Icon name="trash" className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Analyze Button - separate from picker */}
        {selectedPcap && (
          <div className="flex items-center">
            <button
              onClick={handleAnalyze}
              onDoubleClick={(e) => e.preventDefault()} // Prevent double-click
              className={`px-5 py-1 text-sm rounded-lg transition-all duration-300 shadow-md flex items-center space-x-2 transform ${
                isButtonDisabled
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 scale-105 animate-pulse'
                  : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 hover:scale-105'
              } text-white disabled:cursor-not-allowed disabled:opacity-70`}
              disabled={isButtonDisabled}
              title={
                analyzePcapMutation.isPending ? 'Starting analysis...' :
                isAnalysisRunning ? `Analysis running (${progressData?.phase})...` :
                isAnalysisInitiated ? 'Analysis initiated...' :
                'Analyze selected PCAP with network replay'
              }
            >
              <Icon
                name={isButtonDisabled ? "loader" : "activity"}
                className={`w-4 h-4 ${isButtonDisabled ? 'animate-spin' : ''}`}
              />
              <span>
                {analyzePcapMutation.isPending ? 'Starting Analysis...' :
                 isAnalysisRunning ? `Analyzing (${progressData?.phase})...` :
                 'Analyze PCAP'}
              </span>
            </button>

            {/* Stop Button - separated from Analyze button - only show when actually running */}
            {isAnalysisRunning && (
              <button
                onClick={handleStopAnalysis}
                className="ml-6 rounded transition-all hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 group"
                disabled={stopPcapReplayMutation.isPending || isStopInitiated || stopPcapReplayMutation.isLoading}
                title={stopPcapReplayMutation.isPending || isStopInitiated ? "Stopping..." : "Stop PCAP replay analysis"}
              >
                <div className={`w-4 h-4 bg-red-500 rounded-sm transition-all duration-300 group-hover:bg-red-700 group-hover:scale-110 group-hover:shadow-lg ${stopPcapReplayMutation.isPending || isStopInitiated ? 'animate-spin' : 'animate-pulse'}`} />
              </button>
            )}
          </div>
        )}

        {/* Loading States */}
        {removePcapMutation.isPending && (
          <span className="text-sm text-gray-500">Removing...</span>
        )}

        {/* Success Message
        {showSuccessMessage && !isAnalysisRunning && (
          <div className="flex items-center space-x-2 text-sm text-green-600 animate-fade-in">
            <Icon name="check-circle" className="w-4 h-4" />
            <span>Analysis request sent successfully!</span>
          </div>
        )} */}

        {/* Analysis Status */}
        {isAnalysisRunning && progressData && (
          <div className="flex items-center space-x-2 text-sm text-blue-600">
            <Icon name="activity" className="w-4 h-4 animate-pulse" />
            <span className="capitalize">{progressData.phase} - {Math.round(progressData.progress * 100)}%</span>
          </div>
        )}
      </div>
    </div>
  )
}