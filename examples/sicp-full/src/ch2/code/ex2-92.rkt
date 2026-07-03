#lang sicp

;; insertion sort from https://gist.github.com/miyukino/5652107
(define (insert L M comp)
	(if (null? L) M
		(if (null? M) L
			(if (comp (car L) (car M))
				(cons (car L) (insert (cdr L) M comp))
				(cons (car M) (insert (cdr M) L comp))))))
(define (insertionsort L comp)
	(if (null? L) '()
		(insert (list (car L)) (insertionsort (cdr L) comp) comp)))
(define sort insertionsort)

(define (symbol<? s1 s2)
  (string<? (symbol->string s1) (symbol->string s2)))
(define (symbol=? s1 s2)
  (string=? (symbol->string s1) (symbol->string s2)))



(define pi 3.14159)
(define (square x) (* x x))
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
;; get and put definitions
(define operation-table '())

(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

(define (assoc-op key records)
   (cond ((null? records) #f)
         ((equal? key (caar records)) (car records))
         (else (assoc-op key (cdr records)))))

(define (put op type-tags proc)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
           (let ((proc-pair-entry (assoc type-tags proc-list)))
             (if proc-pair-entry
                 (set-cdr! proc-pair-entry proc)
                 (set-car! (cdr op-list-entry)
                           (cons (cons type-tags proc) proc-list)))))
        (set! operation-table
              (cons (list op (list (cons type-tags proc)))
                    operation-table)))))

(define (get op type-tags)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
          (let ((proc-pair-entry (assoc type-tags proc-list)))
            (if proc-pair-entry
                (cdr proc-pair-entry)
                #f)))
        #f)))

;; Modified for ex2-78. 
(define (attach-tag type-tag contents)
  (if (equal? type-tag 'scheme-number) 
      contents
      (cons type-tag contents)))
(define (type-tag datum)
  (cond ((pair? datum) (car datum))
        ((number? datum) 'scheme-number)
        (else (error "Bad tagged datum: TYPE-TAG" datum))))
(define (contents datum)
  (cond ((pair? datum) (cdr datum))
        ((number? datum) datum)
        (else (error "Bad tagged datum: CONTENTS" datum))))
(define (apply-generic op . args)
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (error
            "No method for these types: APPLY-GENERIC"
            (list op type-tags))))))


;; Number package
(define (install-scheme-number-package)
  (define (tag x)
    (attach-tag 'scheme-number x))
  (put 'add '(scheme-number scheme-number)
       (lambda (x y) (tag (+ x y))))
  (put 'sub '(scheme-number scheme-number)
       (lambda (x y) (tag (- x y))))
  (put 'mul '(scheme-number scheme-number)
       (lambda (x y) (tag (* x y))))
  (put 'div '(scheme-number scheme-number)
       (lambda (x y) (tag (/ x y))))
  (put 'make 'scheme-number
       (lambda (x) (tag x)))
  (put '=zero? '(scheme-number)
       (lambda (x) (= x 0)))
  (put 'negate '(scheme-number)
       (lambda (x) (- x)))
  'done)

(install-scheme-number-package)

(define (make-scheme-number n)
  ((get 'make 'scheme-number) n))

;; ===================================================================
;; ======================== Rational package =========================
;; ===================================================================

(define (install-rational-package)
  ;; internal procedures
  (define (numer x) (car x))
  (define (denom x) (cdr x))
  (define (make-rat n d)
    (let ((g (gcd n d)))
      (cons (/ n g) (/ d g))))
  (define (add-rat x y)
    (make-rat (+ (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (sub-rat x y)
    (make-rat (- (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (mul-rat x y)
    (make-rat (* (numer x) (numer y))
              (* (denom x) (denom y))))
  (define (div-rat x y)
    (make-rat (* (numer x) (denom y))
              (* (denom x) (numer y))))

  ;; z1a/z1b = z2a/z2b  iff z1a*z2b - z2a*z1b = 0
  ;; equ? for problem 2.79
  (define (equ? z1 z2)
    (= (- (* (numer z1) (denom z2))
          (* (numer z2) (denom z1)))
        0))
  ;; interface to rest of the system
  (put 'equ? '(rational rational) equ?)
  (define (tag x) (attach-tag 'rational x))
  (put 'add '(rational rational)
       (lambda (x y) (tag (add-rat x y))))
  (put 'sub '(rational rational)
       (lambda (x y) (tag (sub-rat x y))))
  (put 'mul '(rational rational)
       (lambda (x y) (tag (mul-rat x y))))
  (put 'div '(rational rational)
       (lambda (x y) (tag (div-rat x y))))
  (put 'make 'rational
       (lambda (n d) (tag (make-rat n d))))
  ;problem 2.80
  (put '=zero? '(rational)
    (lambda (a) (= (numer a) 0)))
  (put 'negate '(rational)
       (lambda (r) (tag (make-rat (- (numer r)) (denom r)))))
  'done)

(install-rational-package)

(define (make-rational n d)
  ((get 'make 'rational) n d))

;; ===================================================================
;; ================= Complex polar and rectangular ===================
;; ===================================================================

(define (install-polar-package)
  ;; internal procedures
  (define (magnitude z) (car z))
  (define (angle z) (cdr z))
  (define (make-from-mag-ang r a) (cons r a))
  (define (real-part z)
    (* (magnitude z) (cos (angle z))))
  (define (imag-part z)
    (* (magnitude z) (sin (angle z))))
  (define (make-from-real-imag x y)
    (cons (sqrt (+ (square x) (square y)))
          (atan y x)))
  ;; interface to the rest of the system
  (define (tag x) (attach-tag 'polar x))
  (put 'real-part '(polar) real-part)
  (put 'imag-part '(polar) imag-part)
  (put 'magnitude '(polar) magnitude)
  (put 'angle '(polar) angle)
  (put 'make-from-real-imag 'polar
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'polar
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  (put 'negate '(polar)
       (lambda (z) (tag (make-from-mag-ang (magnitude z) (+ (angle z) pi)))))
  'done)
(install-polar-package)

(define (install-rectangular-package)
  ;; internal procedures
  (define (real-part z) (car z))
  (define (imag-part z) (cdr z))
  (define (make-from-real-imag x y)
    (cons x y))
  (define (magnitude z)
    (sqrt (+ (square (real-part z))
             (square (imag-part z)))))
  (define (angle z)
    (atan (imag-part z) (real-part z)))
  (define (make-from-mag-ang r a)
    (cons (* r (cos a)) (* r (sin a))))
  ;; interface to the rest of the system
  (define (tag x)
    (attach-tag 'rectangular x))
  (put 'real-part '(rectangular) real-part)
  (put 'imag-part '(rectangular) imag-part)
  (put 'magnitude '(rectangular) magnitude)
  (put 'angle '(rectangular) angle)
  (put 'make-from-real-imag 'rectangular
       (lambda (x y)
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'rectangular
       (lambda (r a)
         (tag (make-from-mag-ang r a))))
  (put 'negate '(rectangular)
       (lambda (z) (tag (make-from-real-imag (- (real-part z) (- (imag-part z)))))))
  'done)
(install-rectangular-package)

;; ===================================================================
;; ========================= Complex package =========================
;; ===================================================================

(define (install-complex-package)
  ;; imported procedures from rectangular 
  ;; and polar packages
  (define (real-part z)
    (apply-generic 'real-part z))
  (define (imag-part z)
    (apply-generic 'imag-part z))
  (define (magnitude z)
    (apply-generic 'magnitude z))
  (define (angle z)
    (apply-generic 'angle z))

  (define (make-from-real-imag x y)
    ((get 'make-from-real-imag 
          'rectangular) 
     x y))
  (define (make-from-mag-ang r a)
    ((get 'make-from-mag-ang 'polar) 
     r a))
  ;; internal procedures
  (define (add-complex z1 z2)
    (make-from-real-imag 
     (+ (real-part z1) (real-part z2))
     (+ (imag-part z1) (imag-part z2))))
  (define (sub-complex z1 z2)
    (make-from-real-imag 
     (- (real-part z1) (real-part z2))
     (- (imag-part z1) (imag-part z2))))
  (define (mul-complex z1 z2)
    (make-from-mag-ang 
     (* (magnitude z1) (magnitude z2))
     (+ (angle z1) (angle z2))))
  (define (div-complex z1 z2)
    (make-from-mag-ang 
     (/ (magnitude z1) (magnitude z2))
     (- (angle z1) (angle z2))))

  (define (equ? z1 z2) ; for problem 2.79
    (and (= (real-part z1) (real-part z2)) 
         (= (imag-part z1) (imag-part z2))))
  ;; interface to rest of the system
  (put 'equ? '(complex complex) equ?)
  (put 'real-part '(complex) real-part) ; Changes from problem 2.77
  (put 'imag-part '(complex) imag-part)
  (put 'magnitude '(complex) magnitude)
  (put 'angle '(complex) angle)
  (put 'negate '(complex)
       (lambda (z) (tag (apply-generic 'negate z))))

  (define (tag z) (attach-tag 'complex z))
  (put 'add '(complex complex)
       (lambda (z1 z2) 
         (tag (add-complex z1 z2))))
  (put 'sub '(complex complex)
       (lambda (z1 z2) 
         (tag (sub-complex z1 z2))))
  (put 'mul '(complex complex)
       (lambda (z1 z2) 
         (tag (mul-complex z1 z2))))
  (put 'div '(complex complex)
       (lambda (z1 z2) 
         (tag (div-complex z1 z2))))
  (put 'make-from-real-imag 'complex
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'complex
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  ;problem 2.80
  (put '=zero? '(complex)
    (lambda (z) (and (= (real-part z) 0) (= (imag-part z) 0))))
  'done)

(install-complex-package)

(define (=zero? a)
  (apply-generic '=zero? a))
(define (real-part z)
  (apply-generic 'real-part z))
(define (imag-part z)
  (apply-generic 'imag-part z))
(define (magnitude z)
  (apply-generic 'magnitude z))
(define (angle z)
  (apply-generic 'angle z))
(define (mul a b)
  (apply-generic 'mul a b))
(define (add a b)
  (apply-generic 'add a b))
(define (sub a b)
  (apply-generic 'sub a b))
(define (equ? a b)
  (apply-generic 'equ? a b))


(define (install-polynomial-package)
  (define (single-order<? so1 so2)
    (or (symbol<? (car so1) (car so2))
        (< (cadr so2) (cadr so1))))
  (define (order<? o1 o2)
    (cond 
      ((null? o1) #f)
      ((null? o2) #t)
      ((< (length o2) (length o1)) #t)
      ((< (length o1) (length o2)) #f)
      ((single-order<? (car o1) (car o2)) #t)
      ((single-order<? (car o2) (car o1)) #f)
      (else (order<? (cdr o1) (cdr o2)))))

  ;; Term list should be a list of (list coeff monomial)
  ;; monomial is of the form '((x 3) (y 2) (z 4)) to represent x^3*y^2*z^4.
  (define (make-mono coeff order) (list coeff order)) 
  (define (coeff mono) (car mono))
  (define (order mono) (cadr mono))
  (define (make-poly-from-unsorted term-list)
    (define (sort-monomial mono) 
      (make-mono (coeff mono) (sort (order mono) single-order<?)))
    (define (monomial-compare x y) 
      (order<? (order x) (order y)))
    (sort (map sort-monomial term-list) monomial-compare))




  ;; negate
  (define (negate polynomial) 
    (map (lambda (mono) 
           (make-mono (apply-generic 'negate (coeff mono)) 
                      (order mono))) polynomial))


  (define (empty-polynomial? poly) 
    (null? poly))
  (define (first-monomial poly) 
    (car poly))
  (define (rest-monomials poly) 
    (cdr poly))
  (define (adjoin-term term polynomial)
    (if (apply-generic '=zero? (coeff term))
      polynomial
      (cons term polynomial)))
  ;; add-poly
  (define (add-polys L1 L2)
    (cond 
      ((empty-polynomial? L1) L2)
      ((empty-polynomial? L2) L1)
      (else
       (let ((t1 (first-monomial L1))
             (t2 (first-monomial L2)))
         (cond 
           ((order<? (order t1) (order t2) )
            (adjoin-term
             t1
             (add-polys (rest-monomials L1)
                        L2)))
           ((order<? (order t2) (order t1))
            (adjoin-term
             t2
             (add-polys
              L1
              (rest-monomials L2))))
           (else
            (adjoin-term
             (make-mono
  ;(define (make-mono coeff order) (list coeff order)) 
              (apply-generic 'add (coeff t1)
                                  (coeff t2)) 
              (order t1))
             (add-polys
              (rest-monomials L1)
              (rest-monomials L2)))))))))
  (define (sub-polys p1 p2)
    (add-polys p1 (negate p2)))


  (define (adjoin-order single-order order)
    (if (= (cadr single-order) 0)
      order
      (cons single-order order)))
  (define (add-orders o1 o2)
    (cond 
      ((null? o1) o2)
      ((null? o2) o1)
      (else
       (let ((so1 (car o1))
             (so2 (car o2)))
         (cond
           ((symbol<? (car so1) (car so2))
            (adjoin-order
             so1
             (add-orders (cdr o1)
                          o2)))
           ((symbol<? (car so2) (car so1))
            (adjoin-order
             so2
             (add-orders
              o1
              (cdr o2))))
           (else
            (adjoin-order
             (list
              (car so1)
              (+ (cadr so1) (cadr so2)))
             (add-orders
              (cdr o1)
              (cdr o2)))))))))
  ;; mul-poly
  (define (mul-mono-by-poly m1 P)
    (define (mul-mono-by-poly-inner m1 P)
      (if (empty-polynomial? P)
        '()
        (let ((m2 (first-monomial P)))
          (adjoin-term
           (make-mono
            (apply-generic 'mul (coeff m1) (coeff m2))
            (add-orders (order m1) (order m2)))
           ;; If m2 < m3, does m1*m2 < m1*m3? 
           ;; NO! 
           ;; '((a 3)) < '((b 3))  <-- true
           ;; '((a 3)) * '((a 1)) = '((a 4))
           ;; '((b 3)) * '((a 1)) = '((a 1) (b 3))
           ;; So with my definition, '((a 1) (b 3)) < '((a 4))
           ;; Therefore, we need to make sure we sort the result.
           (mul-mono-by-poly-inner
            m1
            (rest-monomials P))))))
    (make-poly-from-unsorted (mul-mono-by-poly-inner m1 P)))
  (define (mul-polys P1 P2)
    (if (empty-polynomial? P1)
      '()
      (add-polys
       (mul-mono-by-poly
        (first-monomial P1) P2)
       (mul-polys (rest-monomials P1) P2))))

  (define (tag p) (attach-tag 'polynomial p))
  (put 'make 'polynomial
       (lambda (terms) 
         (tag (make-poly-from-unsorted terms))))
  (put 'negate '(polynomial)
       (lambda (p) (tag (negate p))))
  (put 'add '(polynomial polynomial)
       (lambda (p1 p2) (tag (add-polys p1 p2))))
  (put 'sub '(polynomial polynomial)
       (lambda (p1 p2) 
         (tag (sub-polys p1 p2))))
  (put 'mul '(polynomial polynomial)
       (lambda (p1 p2) (tag (mul-polys p1 p2))))
  'done)

(install-polynomial-package)

(define (make-polynomial terms)
  ((get 'make 'polynomial) terms))


(define l1 '((x 2) (y 1)))
(define l2 '((x 2) (y 2)))
;;(define l3 (sort '((x 2) (y 2) (b 10) (a 4)) single-order<?))
(define l3 '((x 2) (y 2) (b 10) (a 4)))
(define l4 '())

(define p1 (make-polynomial (list (list 1 l1) (list -1 l2) (list 3 l3) (list -10 l4))))
(define p2 (apply-generic 'negate p1))
(define p3 (make-polynomial '((1 ((x 3))) (1 ((x 1))))))
(define p4 (make-polynomial '((1 ((x 2))) (1 ()) (-1 ((y 1))))))
(define p5 (make-polynomial '((1 ((x 4))) (1 ((x 3))) (1 ((x 2))) (1 ((x 1))) (1 ()))))
(define p6 (make-polynomial '((1 ((x 1))) (-1 ()))))
;;p1
;;p2
(apply-generic 'add p1 p3)
;;(apply-generic 'add p1 p1)
;;(apply-generic 'add p1 p1)
(display "(x^3+x)(x^2-y+1) = -x^3y -xy + x^5 + 2x^3 + x^2 + x") (newline)
(apply-generic 'mul p3 p4)
(display "(x^4+x^3+x^2+x+1)(x-1) = x^5 - 1") (newline)
(apply-generic 'mul p5 p6)
