import classNames from 'classnames'

const { useCallback } = require('react')
const { default: ReactSlider } = require('react-slider')

export default function Slider ({ id, className, label, currentValue, setCurrentValue, min = 0, max = 1, step = 0.1 }) {
  const handleChange = useCallback((v) => {
    console.log(id, v)
    setCurrentValue({ id, v })
  }, [id])
  return (
    <div className={classNames('h-20', className)}>
      <div className='pb-2 text-sm'>{label}</div>
      <ReactSlider
        min={min}
        max={max}
        onAfterChange={handleChange}
        defaultValue={currentValue}
        trackClassName='mt-3 h-[1px] bg-slate-300'
        thumbClassName='w-6 h-6 text-sm text-slate-900 bg-slate-100 text-center'
        renderThumb={(props, state) => <div {...props}>{state.valueNow}</div>}
        step={step}
      />
    </div>
  )
}
