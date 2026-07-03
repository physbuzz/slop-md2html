#lang sicp

(define (entry tree) (car tree))
(define (left-branch tree) (cadr tree))
(define (right-branch tree) (caddr tree))
(define (make-tree entry left right)
  (list entry left right))
;; trivial tree
(define (tt entry)
  (list entry '() '()))

(define one (tt 1))
(define three (tt 3))
(define five (tt 5))
(define seven (tt 7))
(define nine (tt 9))
(define eleven (tt 11))
(define tree-one (make-tree 7 (make-tree 3 one five) (make-tree 9 '() eleven)))
(define tree-two (make-tree 3 one (make-tree 7 five (make-tree 9 '() eleven))))
(define tree-three (make-tree 5 (make-tree 3 one '()) (make-tree 9 seven eleven)))

(define (element-of-set? x set)
  (cond ((null? set) false)
        ((= x (entry set)) true)
        ((< x (entry set))
         (element-of-set? 
          x 
          (left-branch set)))
        ((> x (entry set))
         (element-of-set? 
          x 
          (right-branch set)))))

(define (adjoin-set x set)
  (cond ((null? set) (make-tree x '() '()))
        ((= x (entry set)) set)
        ((< x (entry set))
         (make-tree
          (entry set)
          (adjoin-set x (left-branch set))
          (right-branch set)))
        ((> x (entry set))
         (make-tree
          (entry set)
          (left-branch set)
          (adjoin-set x (right-branch set))))))

;; Each time we do an append we have to traverse a linked list, 
;; which is of length n, so I think

;; If it's a balanced tree, at step 1 we do (n/2) steps
;; T(tree) = Length(left-tree) + T(left-tree)+ 1 + T(right-tree)
;; T(N) = N/2 + 2 T(N/2) + 1
(define (tree->list-1 tree)
  (if (null? tree)
      '()
      (append 
       (tree->list-1 
        (left-branch tree))
       (cons (entry tree)
             (tree->list-1 
              (right-branch tree))))))

;; Theta(# of nodes?)
(define (tree->list-2 tree)
  ;; Invariant: tree < result-list (for all elements)
  (define (copy-to-list tree result-list)
    (if (null? tree)
        result-list
        (copy-to-list 
         (left-branch tree)
         (cons (entry tree)
               (copy-to-list 
                (right-branch tree)
                result-list)))))
  (copy-to-list tree '()))

(tree->list-1 tree-one)
(tree->list-2 tree-one)
(tree->list-1 tree-two)
(tree->list-2 tree-two)
(tree->list-1 tree-three)
(tree->list-2 tree-three)
