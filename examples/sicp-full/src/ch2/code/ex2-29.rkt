#lang sicp

;; part 1
(define (make-mobile left right)
  (list left right))
(define (left-branch mobile) (car mobile))
(define (right-branch mobile) (car (cdr mobile)))

(define (make-branch length mobile)
  (list length mobile))
(define (branch-length branch) (car branch))
(define (branch-mobile branch) (car (cdr branch)))
(define (branch-leaf? branch) (not (pair? (branch-mobile branch))))

;; part 2
(define (total-weight mobile) 
  (if (pair? mobile) 
    (+ (total-weight (branch-mobile (left-branch mobile))) 
       (total-weight (branch-mobile (right-branch mobile))))
    mobile))


;; part 3
(define (torque mobile)
  (let ((left  (left-branch mobile))
        (right (right-branch mobile)))
    (- (* (branch-length left) 
          (total-weight (branch-mobile left)))
       (* (branch-length right) 
          (total-weight (branch-mobile right))))))

(define (echo x)
  (display x) (newline) x)

(define (balanced? mobile)
  (if (pair? mobile) 
    (and (= (torque mobile) 0)
      (balanced? (branch-mobile (left-branch mobile)))
      (balanced? (branch-mobile (right-branch mobile))))
    #t))
  
;; total weight 5
(define x1 (make-mobile (make-branch 4 1) (make-branch 1 4)))
;; total weight 4
(define x2 (make-mobile (make-branch 2 3) (make-branch 6 1)))
;; total weight 8
(define x3 (make-mobile (make-branch 1 x2) (make-branch 1 x2)))
;; total weight 20
(define x4 (make-mobile (make-branch 8 4) (make-branch 2 16)))
;; Total weight 13
(define x5 (make-mobile (make-branch 4 x1) ;; torque 20
             (make-branch 20/8 x3)))
(define x6 (make-mobile
            (make-branch 2 x4) ;; torque of 40
            (make-branch 40/13 x5))) 

(define y1 (make-mobile (make-branch 5 1) (make-branch 3 10)))

;; All the x's should be balanced
(balanced? x1)
(balanced? x2)
(balanced? x3)
(balanced? x4)
(balanced? x5)
(balanced? x6)
;; And y isn't.
(balanced? y1)
