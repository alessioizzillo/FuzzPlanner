import { useState } from 'react'
import { useGetPcaps, useRemovePcap, useAnalyzePcap } from '@/hooks/queries'
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
import AnalysisProgress from '@/components/AnalysisProgress'

export default function PcapPicker () {
  const firmwareId = useSelectedFirmware()
  const brandId = useSelectedBrand()
  const selectedPcap = useSelectedPcap()
  const setSelectedPcap = useSetSelectedPcap()
  const resetSelectedPcap = useResetSelectedPcap()
  const [analysisContainerName, setAnalysisContainerName] = useState(null)
  const [showSuccessMessage, setShowSuccessMessage] = useState(false)

  const { isLoading, isError, error, data: pcaps, refetch } = useGetPcaps(brandId, firmwareId)
  const removePcapMutation = useRemovePcap()
  const analyzePcapMutation = useAnalyzePcap()

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
    if (!selectedPcap) return

    try {
      // Show success message immediately
      setShowSuccessMessage(true)
      setTimeout(() => setShowSuccessMessage(false), 3000) // Hide after 3 seconds

      const response = await analyzePcapMutation.mutateAsync({
        brandId,
        firmwareId,
        pcapName: selectedPcap
      })

      // Extract container name from response for progress tracking
      if (response.container_name) {
        setAnalysisContainerName(response.container_name)
      }
    } catch (error) {
      console.error('Failed to analyze PCAP:', error)
      setAnalysisContainerName(null)
      setShowSuccessMessage(false) // Hide success message on error
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
          <button
            onClick={handleAnalyze}
            className={`px-5 py-1 text-sm rounded-lg transition-all duration-300 shadow-md flex items-center space-x-2 transform ${
              analyzePcapMutation.isPending
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 scale-105 animate-pulse'
                : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 hover:scale-105'
            } text-white disabled:cursor-not-allowed`}
            disabled={analyzePcapMutation.isPending}
            title={analyzePcapMutation.isPending ? 'Analysis in progress...' : 'Analyze selected PCAP with network replay'}
          >
            <Icon
              name={analyzePcapMutation.isPending ? "loader" : "activity"}
              className={`w-4 h-4 ${analyzePcapMutation.isPending ? 'animate-spin' : ''}`}
            />
            <span>
              {analyzePcapMutation.isPending ? 'Analysis Started!' : 'Analyze PCAP'}
            </span>
          </button>
        )}

        {/* Loading States */}
        {removePcapMutation.isPending && (
          <span className="text-sm text-gray-500">Removing...</span>
        )}

        {/* Success Message */}
        {showSuccessMessage && (
          <div className="flex items-center space-x-2 text-sm text-green-600 animate-fade-in">
            <Icon name="check-circle" className="w-4 h-4" />
            <span>Analysis request sent successfully!</span>
          </div>
        )}
      </div>

      {/* Progress Visualization */}
      {analysisContainerName && (
        <AnalysisProgress containerName={analysisContainerName} />
      )}
    </div>
  )
}