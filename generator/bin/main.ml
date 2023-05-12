open Ast
open Generator
open Write 

let n = Sys.argv.(1) |> int_of_string
let seed = Sys.argv.(2) |> int_of_string

(** Generates a random AST from [seed]. *)
let generate_random_ast seed =
  let distribution = random_distribution seed in
  let ast = random_ast seed 0 distribution in
  let prg = program (string_of_expr ast) in
  let filename = "generated/" ^ (string_of_int seed) ^ ".c" in
  write_file filename prg

let () = 
  if seed = 0 then
    (Random.self_init ();
    for _ = 1 to n do
      let random_seed = Random.bits () in
      generate_random_ast random_seed
    done)
  else
    generate_random_ast seed
    