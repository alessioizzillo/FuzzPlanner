import { Fragment } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import { ArrowUturnLeftIcon, CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid'

export default function Picker ({ items, selected, setSelected, resetSelected, placeholder }) {
  return (
    <div className='flex items-center w-72'>
      <Listbox value={selected || ''} onChange={setSelected}>
        <div className='relative w-4/5'>
          <Listbox.Button className='relative w-full py-2 pl-3 pr-10 text-left rounded-lg shadow-md cursor-pointer bg-slate-700 focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm'>
            <span className='block truncate'>{selected || placeholder}</span>
            <span className='absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none'>
              <ChevronUpDownIcon
                className='w-5 h-5 text-gray-400'
                aria-hidden='true'
              />
            </span>
          </Listbox.Button>
          <Transition
            as={Fragment}
            leave='transition ease-in duration-100'
            leaveFrom='opacity-100'
            leaveTo='opacity-0'
          >
            <Listbox.Options className='absolute z-10 w-full py-1 mt-1 overflow-auto text-base rounded-md shadow-lg bg-slate-200 max-h-60 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm'>
              {items.map((item, itemIdx) => (
                <Listbox.Option
                  key={itemIdx}
                  className={({ active }) => `relative cursor-pointer select-none py-2 pl-10 pr-4 ${active ? 'bg-amber-100 text-amber-900' : 'text-gray-900'}`}
                  value={item.id}
                >
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                        {item.label}
                      </span>
                      {selected
                        ? (
                          <span className='absolute inset-y-0 left-0 flex items-center pl-3 text-amber-600'>
                            <CheckIcon className='w-5 h-5' aria-hidden='true' />
                          </span>
                          )
                        : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
      <ArrowUturnLeftIcon className='w-5 h-5 ml-2 text-gray-400 cursor-pointer' onClick={resetSelected} />
    </div>
  )
}
