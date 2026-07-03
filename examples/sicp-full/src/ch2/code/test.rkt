#lang sicp



;; Return false if element doesn't exist
;; Return list otherwise.
(define (take-after elem lst)
  (let ((rst (memq elem lst)))
    (if (eq? rst #f) rst (cdr rst))))

;; Return false if element doesn't exist
;; Return list otherwise.
(define (take-before elem lst)
  (cond ((null? lst) #f)
        ((eq? (car lst) elem) nil)
        (else (let ((rst (take-before elem (cdr lst))))
                (if (not rst) 
                  rst 
                  (cons (car lst) rst))))))

;; True if a '+ exists in our expression.
(define (sum? x)
  (and (pair? x) (not (eq? (memq '+ x) #f))))
;; Take from the first symbol, up to but excluding '+
(define (addend s)
  (take-before '+ s)) 
;; Exclude the first terms up to '+ and return the rest (?)
(define (augend s) 
  (take-after '+ s)) 
;; True if no '+ exists in our expression, but '* does.
(define (product? x)
  (and (pair? x) 
       (not (sum? x)) 
       (not (eq? (memq '* x) #f))))
;; take up to and excluding the first '*
(define (multiplier p) 
  (take-before '* p))
;; Get the rest after the first '*
(define (multiplicand p) 
  (take-after '* p))









