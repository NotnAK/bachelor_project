// src/components/SmartSearchClassFilter.js

import React from 'react'
import { FaTimesCircle } from 'react-icons/fa'

export default function SmartSearchClassFilter({
  showClassFilter,
  newClassInput,
  setNewClassInput,
  handleAddClass,
  classFilterList,
  handleRemoveClass,
  isApplyingClassFilter,
  applyClassFilter
}) {
  return (
    <>
      {showClassFilter && (
        <div className="mb-3">
          <div className="d-flex gap-2 align-items-center">
            {/* Поле для ввода одного класса */}
            <input
              type="text"
              className="form-control form-control-sm"
              placeholder="Enter a class (e.g. dog)"
              value={newClassInput}
              onChange={e => setNewClassInput(e.target.value)}
            />
            {/* Кнопка «Add» */}
            <button
              className="btn btn-primary btn-sm"
              disabled={newClassInput.trim() === '' || classFilterList.length >= 4}
              onClick={handleAddClass}
            >
              Add
            </button>
          </div>

          {/* Список «пилочек» добавленных классов */}
          <div className="mt-2">
            {classFilterList.map((cls, idx) => (
              <span
                key={idx}
                className="badge bg-secondary text-white me-1 mb-1"
                style={{ fontSize: '0.9rem', padding: '0.4rem 0.6rem' }}
              >
                {cls}{' '}
                <FaTimesCircle
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleRemoveClass(cls)}
                />
              </span>
            ))}
          </div>

          {/* Кнопка «Apply» */}
          <div className="mt-2">
            <button
              className="btn btn-success btn-sm"
              disabled={isApplyingClassFilter}
              onClick={applyClassFilter}
            >
              {isApplyingClassFilter ? (
                <span className="spinner-border spinner-border-sm" role="status" />
              ) : (
                'Apply'
              )}
            </button>
            {/* Подсказка, сколько ещё можно добавить */}
            <small className="text-muted ms-2">
              {classFilterList.length}/4 added
            </small>
          </div>
        </div>
      )}
    </>
  )
}
