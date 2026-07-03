#lang sicp

(define (make-from-mag-ang r a)
  (define (dispatch op)
    (cond ((eq? op 'real-part) (* r (cos a)))
          ((eq? op 'imag-part) (* r (sin a)))
          ((eq? op 'magnitude) r)
          ((eq? op 'angle) a)
          (else
           (error "Unknown op: 
            MAKE-FROM-MAG-ANGLE" op))))
  dispatch)

(define (apply-generic op arg) (arg op))

(define my-c (make-from-mag-ang (sqrt 2) (/ 3.14159 4)))

(apply-generic 'real-part my-c)
(apply-generic 'imag-part my-c)
