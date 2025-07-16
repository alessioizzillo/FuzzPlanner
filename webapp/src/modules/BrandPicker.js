import { useSelectedBrand, useSetSelectedBrand, useResetSelectedBrand } from '@/hooks/store/selectedBrand'
import { useGetBrands } from '@/hooks/queries'
import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function BrandPicker () {
    const selectedBrand = useSelectedBrand()
    const setSelectedBrand = useSetSelectedBrand()
    const resetSelectedBrand = useResetSelectedBrand()
    const { isLoading, isError, error, data } = useGetBrands()
  
    if (isLoading) return <Spinner />
    if (isError) return <Error error={error} />
    if (!data || data.length === 0) return <div>No brands found</div>
  
    const handleSelect = id => {
      setSelectedBrand(id)
    }
  
    return (
      <Picker
        items={data.map(brand => ({ id: brand, label: brand }))}
        selected={selectedBrand}
        setSelected={handleSelect}
        resetSelected={resetSelectedBrand}
        placeholder='Select a brand...'
      />
    )
  }
  
