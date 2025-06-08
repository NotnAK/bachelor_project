// src/components/SmartSearchHelpModal.js

import React from 'react'

export default function SmartSearchHelpModal({ showHelpModal, closeHelpModal }) {
  return (
    <>
      {showHelpModal && (
        <div
          className="modal d-block"
          tabIndex="-1"
          role="dialog"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
        >
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Help</h5>
                <button
                  type="button"
                  className="btn-close"
                  aria-label="Close"
                  onClick={closeHelpModal}
                />
              </div>
              <div className="modal-body">
                <p>
                  <strong>Search:</strong> Performs a <em>vector-based</em> search of paintings. It retrieves
                  images most similar to your query using embeddings.
                </p>
                <p>
                  <strong>Use VQA:</strong> When checked, the system will use Visual Question Answering (VQA) on
                  each candidate painting. In this mode, Paligemma answers “does this image contain &lt;your
                  query&gt;?” and only paintings with a “yes” answer will be returned.
                </p>
                <p>
                  <strong>Sort by AI Description:</strong> When unchecked, results are sorted purely by image
                  similarity. If you enable this checkbox, results will be re-ranked by combining image
                  similarity and similarity between your query and the AI-generated text description of each
                  painting. Use the slider to adjust the weight.
                </p>
                <p>
                  <strong>Class Filter:</strong> Opens a small input field where you can type one
                  object class at a time and click “Add.” You may add up to 4 unique classes in total. The
                  added classes appear as pills with “×” to remove. After adding desired classes, click
                  “Apply” to send them to the server for filtering (only paintings containing at least 75%
                  of your specified classes will remain).
                </p>
                <p>
                  <strong>Genre / Year / Artist Filters:</strong> After receiving search results, you can further
                  narrow down the list by selecting a genre, a year, or an artist from the dropdown menus.
                </p>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={closeHelpModal}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
