#include <iostream>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <unordered_set>
#include <vector>

#define MEMORYSIZE 65536
#define CODESIZE 65536
#define uint8 unsigned char
#define uint16 unsigned short

long c;                // char variable for fgetc() / getchar()
uint16 p = 0,          // the pointer of code line
    q = 0;             // the pointer of instruction
uint8 reg[26];         // registers from A to Z
uint8 mem[MEMORYSIZE]; // memory
FILE *program,         // FILE * for code
    *input;            // FILE * for input

struct instruct {
  uint8 src_mode, dest_mode; // 0 - Imm
                             // 1 - Register
                             // 2 - [Register]
                             // 3 - [Register + Imm]
                             // 4 - [Register + Register]
                             // 5 - [Imm]
  uint16 src, dest, src_offset, dest_offset;
  uint16 line;
} code[CODESIZE];

void err(std::string s) {
  fprintf(stderr, "Error detected at line %hu: %s\n", p, s.c_str());
  fclose(input);
  exit(1);
}

std::vector<std::string> raw_codes(1);

void preprocess() {
  char *line = NULL;
  char src[16] = "", dest[16] = "";
  char buf1[2] = "", buf2[2] = "";
  int buf3 = 0;
  size_t len = 0;
  ssize_t read;
  while ((read = getline(&line, &len, program)) != -1) {
    p++;
    raw_codes.push_back(std::string(line));
    if (line[0] == '#' || line[0] == '\r' || line[0] == '\n')
      continue;
    if (sscanf(line, "%*[ |\t]%[^<]<%[^ |\t|\r|\n]", dest, src) != 2)
      if (sscanf(line, "%[^<]<%[^ |\t|\r|\n]", dest, src) != 2)
        err("Syntax Error");

    if (src[0] == '[') {
      if (sscanf(src, "[%1[A-Z]+%1[A-Z]", buf1, buf2) == 2) {
        code[q].src_mode = 4;
        code[q].src = buf1[0] - 'A';
        code[q].src_offset = buf2[0] - 'A';
        if (code[q].src_offset == 8 || code[q].src_offset == 14)
          err("I/O can't be used here");
      } else if (sscanf(src, "[%1[A-Z]+%d", buf1, &buf3) == 2) {
        code[q].src_mode = 3;
        code[q].src = buf1[0] - 'A';
        code[q].src_offset = (uint16)buf3;
      } else if (sscanf(src, "[%1[A-Z]", buf1) == 1) {
        code[q].src_mode = 2;
        code[q].src = buf1[0] - 'A';
        code[q].src_offset = 0;
      } else if (sscanf(src, "[%d", &buf3) == 1) {
        code[q].src_mode = 5;
        code[q].src = (uint16)buf3;
        code[q].src_offset = 0;
      } else {
        err("Syntax Error");
      }
      if ((code[q].src == 8 || code[q].src == 14) && code[q].src_mode != 5)
        err("I/O can't be used here");
    } else if (src[0] >= 'A' && src[0] <= 'Z') {
      code[q].src_mode = 1;
      code[q].src = src[0] - 'A';
      code[q].src_offset = 0;
      if (code[q].src == 14)
        err("O can't be used as src");
    } else if (sscanf(src, "%d", &buf3) == 1) {
      code[q].src_mode = 0;
      code[q].src = (uint16)buf3;
      code[q].src_offset = 0;
    } else {
      err("Syntax Error");
    }

    if (dest[0] == '[') {
      if (sscanf(dest, "[%1[A-Z]+%1[A-Z]", buf1, buf2) == 2) {
        code[q].dest_mode = 4;
        code[q].dest = buf1[0] - 'A';
        code[q].dest_offset = buf2[0] - 'A';
        if (code[q].dest_offset == 8 || code[q].dest_offset == 14)
          err("I/O can't be used here");
      } else if (sscanf(dest, "[%1[A-Z]+%d", buf1, &buf3) == 2) {
        code[q].dest_mode = 3;
        code[q].dest = buf1[0] - 'A';
        code[q].dest_offset = (uint16)buf3;
      } else if (sscanf(dest, "[%1[A-Z]", buf1) == 1) {
        code[q].dest_mode = 2;
        code[q].dest = buf1[0] - 'A';
        code[q].dest_offset = 0;
      } else if (sscanf(dest, "[%d", &buf3) == 1) {
        code[q].dest_mode = 5;
        code[q].dest = (uint16)buf3;
        code[q].dest_offset = 0;
      } else {
        err("Syntax Error");
      }
      if ((code[q].dest == 8 || code[q].dest == 14) && code[q].dest_mode != 5)
        err("I/O can't be used here");
    } else if (dest[0] >= 'A' && dest[0] <= 'Z') {
      code[q].dest_mode = 1;
      code[q].dest = dest[0] - 'A';
      code[q].dest_offset = 0;
      if (code[q].dest == 8)
        err("I can't be used as dest");
    } else if (sscanf(dest, "%d", &buf3) == 1) {
      err("Dest can't be immediate");
    } else {
      err("Syntax Error");
    }
    code[q].line = p;

    q++;
  }
  free(line);
}

std::unordered_set<uint16> breakpoints;

void WaitForCommand() {
  std::cout << "Waiting for command at line ...\n";
  std::string command;
  while (true) {
    std::cin >> command;
    if (command == "continue") {
      return;
    } else if (command == "add_breakpoint") {
      uint16 bp;
      std::cin >> bp;
      if (bp > p) {
        std::cerr << "Breakpoint out of range\n";
        continue;
      }
      breakpoints.insert(bp);
      continue;
    } else if (command == "remove_breakpoint") {
      uint16 bp;
      std::cin >> bp;
      if (bp > p) {
        std::cerr << "Breakpoint out of range\n";
      }
      breakpoints.erase(bp);
      continue;
    } else if (command == "list_breakpoints") {
      for (const auto &bp : breakpoints) {
        std::cerr << bp << ' ';
      }
      std::cerr << '\n';
      continue;
    } else if (command == "display") {
      std::string data_name;
      std::cin >> data_name;
      if (data_name.size() == 1) {
        if (data_name[0] < 'A' || data_name[0] > 'Z') {
          std::cerr << "Invalid register name\n";
          continue;
        } else {
          std::cerr << data_name[0] << " = " << (int)reg[data_name[0] - 'A']
                    << '\n';
        }
      } else {
        if (data_name[0] != '[' || data_name[data_name.size() - 1] != ']') {
          std::cerr << "Invalid memory access\n";
          continue;
        }
        int offset = 0;
        try {
          offset = std::stoi(data_name.substr(1, data_name.size() - 2));
        } catch (const std::invalid_argument &) {
          std::cerr << "Invalid memory access\n";
          continue;
        }
        if (offset < 0 || offset >= MEMORYSIZE) {
          std::cerr << "Memory access out of range\n";
          continue;
        }
        std::cerr << "Memory[" << offset << "] = " << (int)mem[offset] << '\n';
      }
    } else if (command == "help") {
      std::cout << "Available commands:\n"
                << "  continue - Continue execution\n"
                << "  add_breakpoint <line> - Add a breakpoint at the "
                   "specified line\n"
                << "  remove_breakpoint <line> - Remove a breakpoint at the "
                   "specified line\n"
                << "  list_breakpoints - List all breakpoints\n"
                << "  display <Register ID> - Display the value of a register "
                   "or memory location\n"
                << "  display [<offset>] - Display the value at a specific "
                   "memory offset(offset is a number!)\n"
                << "  help - Show this help message\n";
      continue;
    } else {
      std::cerr << "Unknown command: " << command << '\n';
      continue;
    }
  }
}

int main(int argc, char **argv) {
  if (argc != 3)
    err("Invalid arguments");
  if (!(program = fopen(argv[1], "r")))
    err("Can't open program file");
  if (!(input = fopen(argv[2], "r")))
    err("Can't open input file");
  preprocess();
  WaitForCommand();
  fclose(program);
  while (true) {
    for (uint16 i = 0; i < q; i++) {
      p = code[i].line;
      if (breakpoints.find(p) != breakpoints.end()) {
        std::cerr << "Breakpoint at line " << p << '\n';
        std::cerr << "The next code line is: " << raw_codes[p] << '\n';
        WaitForCommand();
      }
      uint8 src = 0;
      if (code[i].src == 8 && code[i].src_mode == 1) {
        if ((c = fgetc(input)) != EOF)
          src = c;
      } else {
        switch (code[i].src_mode) {
        case 0:
          src = code[i].src;
          break;
        case 1:
          src = reg[code[i].src];
          break;
        case 2:
          src = mem[reg[code[i].src]];
          break;
        case 3:
          src = mem[reg[code[i].src] + code[i].src_offset];
          break;
        case 4:
          src = mem[reg[code[i].src] + reg[code[i].src_offset]];
          break;
        case 5:
          src = mem[code[i].src];
          break;
        default:
          err("Syntax Error");
        }
      }
      if (code[i].dest == 14 && code[i].dest_mode == 1) {
        putchar(src);
      } else if (code[i].dest == 25 && code[i].dest_mode == 1) {
        if (src != 0) {
          fclose(input);
          exit(0);
        }
      } else {
        switch (code[i].dest_mode) {
        case 1:
          reg[code[i].dest] = src;
          break;
        case 2:
          mem[reg[code[i].dest]] = src;
          break;
        case 3:
          mem[reg[code[i].dest] + code[i].dest_offset] = src;
          break;
        case 4:
          mem[reg[code[i].dest] + reg[code[i].dest_offset]] = src;
          break;
        case 5:
          mem[code[i].dest] = src;
          break;
        default:
          err("Syntax Error");
        }
      }
    }
  }

  fclose(input);
  exit(0);
}
