import { useSelectedRunView, useSetSelectedRunViewConfEntry } from '@/hooks/store/selectedRun'
import classNames from 'classnames'
import { useCallback } from 'react'
import ReactSlider from 'react-slider'

function Threshold ({ id, label, currentValue, setCurrentValue }) {
  const handleChange = useCallback((v) => {
    console.log(id, v)
    setCurrentValue({ id, v })
  }, [id])
  return (
    <div className='h-20'>
      <div className='pb-2 text-sm'>{label}</div>
      <ReactSlider
        min={0}
        max={1}
        onAfterChange={handleChange}
        defaultValue={currentValue}
        trackClassName='mt-3 h-[1px] bg-slate-300'
        thumbClassName='w-6 h-6 text-sm text-slate-900 bg-slate-100 text-center'
        renderThumb={(props, state) => <div {...props}>{state.valueNow}</div>}
        step={0.1}
      />
    </div>
  )
}

export default function RunViewConf ({ className }) {
  const selectedRunView = useSelectedRunView()
  const setSelectedRunViewConfEntry = useSetSelectedRunViewConfEntry()
  return (
    <div className={classNames('flex flex-col', className)}>
      <Threshold id='borderThreshold' label='Border' currentValue={selectedRunView.conf.borderThreshold} setCurrentValue={setSelectedRunViewConfEntry} />
      <Threshold id='listenThreshold' label='Listen' currentValue={selectedRunView.conf.listenThreshold} setCurrentValue={setSelectedRunViewConfEntry} />
      <Threshold id='withinThreshold' label='W/R' currentValue={selectedRunView.conf.withinThreshold} setCurrentValue={setSelectedRunViewConfEntry} />
    </div>
  )
}
