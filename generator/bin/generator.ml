open Ast
open Distribution

let max_depth = Sys.argv.(3) |> int_of_string

let random_seed state = 
  Random.State.bits state

(** Generates a random integer literal. *)
let random_int_lit state =
  let n = Random.State.bits64 state in
  IntLit n

(** Generates a random size literal (int in [0, 64]). *)
let random_size_lit state =
  let n = Random.State.full_int state 65 in
  SizeLit n

(** Generates a random boolean leaf (terminal) of the AST. *)
let random_bool_terminal state p = 
  choose_normalized state [True; False] p

(** Generates a random boolean node (non-terminal) of the AST. *)
let rec random_bool_expr state depth p = 
  choose_normalized state [
    lazy True;
    lazy False;

    lazy (Not (random_bool_expr_child state depth p));

    lazy (LessThan (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (LessEqual (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (GreaterThan (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (GreaterEqual (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (Equal (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (NotEqual (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
  ] [ p.true_p; p.false_p; p.not_p;
      p.less_than_p; p.less_equal_p; 
      p.greater_than_p; p.greater_equal_p; 
      p.equal_p; p.not_equal_p ]

and random_bool_expr_child state depth p =
  let seed = random_seed state in
  let state = Random.State.make [|seed|] in 
  if depth >= max_depth then 
    random_bool_terminal state [p.true_p; p.false_p]
  else
    Lazy.force (random_bool_expr state (depth + 1) p)

(** Generates a random arithmetic leaf (terminal) of the AST. *)
and random_arith_terminal state p = 
  choose_normalized state [X; Y; (random_int_lit state)] p

and random_arith_expr state depth p = 
  choose_normalized state [
    lazy X;
    lazy Y;
    lazy (random_int_lit state);

    lazy (Neg (random_arith_expr_child state depth p));
    lazy (Plus (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (Minus (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
    lazy (Times (random_arith_expr_child state depth p, random_arith_expr_child state depth p));
  ] [ p.x_p; p.y_p; p.int_lit_p; 
      p.neg_p; p.plus_p; p.minus_p; p.times_p; ]

and random_arith_expr_child state depth p =
  let seed = random_seed state in
  let state = Random.State.make [|seed|] in 
  if depth >= max_depth then 
    random_arith_terminal state [p.x_p; p.y_p; p.int_lit_p]
  else
    Lazy.force (random_arith_expr state (depth + 1) p)

(** Generates a random leaf (terminal) of the AST. *)
let random_terminal state p = 
  let arith_terminal = random_arith_terminal state [p.x_p; p.y_p; p.int_lit_p] in 
  let bool_terminal = random_bool_terminal state [p.true_p; p.false_p] in
  
  choose_normalized state [
    Aexp arith_terminal;
    Bexp bool_terminal;
  ] [ arith_expr_p p; bool_expr_p p ]

(** Generates a random node (non-terminal) of the AST. *)
let rec random_expr (state: Random.State.t) (depth: int) (p: expr_p) =
  choose_normalized state [
    lazy (Bexp (Lazy.force (random_bool_expr state depth p)));
    lazy (Aexp (Lazy.force (random_arith_expr state depth p)));

    lazy (BitwiseAnd (random_expr_child state depth p, random_expr_child state depth p));
    lazy (BitwiseOr (random_expr_child state depth p, random_expr_child state depth p));
    lazy (BitwiseComplement (random_expr_child state depth p));
    lazy (BitwiseXor (random_expr_child state depth p, random_expr_child state depth p));
    lazy (LeftShift (random_expr_child state depth p, random_size_lit state));
    lazy (RightShift (random_expr_child state depth p, random_size_lit state));
  ] [ bool_expr_p p; arith_expr_p p; 
      p.bitwise_and_p; p.bitwise_or_p; 
      p.bitwise_complement_p; p.bitwise_xor_p; 
      p.left_shift_p; p.right_shift_p ]

and random_expr_child state depth p =
  let seed = random_seed state in
  let state = Random.State.make [|seed|] in 
  if depth >= max_depth then 
    random_terminal state p
  else
    Lazy.force (random_expr state (depth + 1) p)
