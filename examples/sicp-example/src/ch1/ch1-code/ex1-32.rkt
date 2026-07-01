#lang sicp


;(accumulate
; combiner null-value term a next b)
;; It helps to write out sum and product in terms of accumulate first.

(define (product term a next b)
  (accumulate * 1 term a next b))
(define (sum term a next b)
  (accumulate + 0 term a next b))
(define (accumulate combiner null-value term a next b)
  (if (> a b)
    null-value
    (combiner (term a)
      (accumulate combiner null-value term (next a) next b))))

;; Evidently there was no reason for me to define a scoped "iter"
;;    function earlier.
;; (define (accumulate-iter combiner null-value term a next b)
;;   (define (iter a result)
;;     (if (> a b)
;;          result
;;          (iter (next a) (combiner result (term a)))))
;;   (iter a null-value))
(define (accumulate-iter combiner null-value term a next b)
  (if (> a b)
       null-value
       (accumulate-iter combiner 
                       (combiner null-value (term a))
                        term
                        (next a)
                        next
                        b)))
(define (sum-iter term a next b)
  (accumulate-iter + 0 term a next b))

(define (add-one n)
  (+ n 1))
(define (my-term n)
  (/ 6.0 (* n n)))
; Should be pi
(sqrt (sum my-term 1 add-one 10000))
(sqrt (sum-iter my-term 1 add-one 10000))

