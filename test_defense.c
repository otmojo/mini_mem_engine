#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    void *ptr;
    size_t size;
} MemEntry;

typedef struct {
    int *data;
    int size;
    int cap;
} t_vec;

#define MAX_ALLOC 10000
MemEntry g_table[MAX_ALLOC];
int g_count = 0;

void fatal_error(const char *msg) {
    fprintf(stderr, "\n===== FATAL SYSTEM ERROR =====\n");
    fprintf(stderr, "%s\n", msg);
    fprintf(stderr, "==============================\n");
    abort();
}

void vec_assert_valid(t_vec *v) {
    if (v == NULL)
        fatal_error("Vector pointer is NULL");
    if (v->data == NULL)
        fatal_error("Vector data pointer is NULL");
    if (v->cap <= 0)
        fatal_error("Vector capacity must be > 0");
    if (v->size < 0)
        fatal_error("Vector size cannot be negative");
    if (v->size > v->cap)
        fatal_error("Vector size exceeds capacity (Invariant violated)");
}

void *mt_malloc(size_t size) {
    if (size == 0)
        fatal_error("Cannot allocate 0 bytes");
    if (g_count >= MAX_ALLOC)
        fatal_error("Memory tracking table full - too many allocations");
    
    void *ptr = malloc(size);
    if (!ptr)
        fatal_error("malloc() failed - out of memory");
    
    g_table[g_count].ptr = ptr;
    g_table[g_count].size = size;
    g_count++;
    
    return ptr;
}

void mt_free(void *ptr) {
    if (!ptr) return;
    
    for (int i = 0; i < g_count; i++) {
        if (g_table[i].ptr == ptr) {
            free(ptr);
            g_table[i].ptr = NULL;
            g_table[i].size = 0;
            
            for (int j = i; j < g_count - 1; j++) {
                g_table[j] = g_table[j + 1];
            }
            g_count--;
            return;
        }
    }
    
    fatal_error("Double free or untracked pointer detected!");
}

int vec_push(t_vec *v, int val) {
    vec_assert_valid(v);
    
    if (v->size == v->cap) {
        if (v->cap > (1 << 30)) {
            fprintf(stderr, "ERROR: Vector capacity overflow attempted: %d\n", v->cap);
            return -1;
        }
        
        int new_cap = v->cap * 2;
        
        if (new_cap <= v->cap || new_cap <= 0) {
            fatal_error("Integer overflow detected during capacity doubling");
        }
        
        if (new_cap > (1 << 30)) {
            fprintf(stderr, "ERROR: Requested allocation too large: %d * 4 bytes\n", new_cap);
            return -1;
        }
        
        int *new_data = mt_malloc(sizeof(int) * new_cap);
        if (!new_data) return -1;
        
        for (int i = 0; i < v->size; i++) {
            new_data[i] = v->data[i];
        }
        
        int *old_data = v->data;
        v->data = new_data;
        v->cap = new_cap;
        
        mt_free(old_data);
    }
    
    v->data[v->size++] = val;
    vec_assert_valid(v);
    return 0;
}

t_vec *vec_create(int init_cap) {
    if (init_cap <= 0)
        fatal_error("Vector initial capacity must be > 0");
    
    t_vec *v = (t_vec *)mt_malloc(sizeof(t_vec));
    v->data = (int *)mt_malloc(sizeof(int) * init_cap);
    v->size = 0;
    v->cap = init_cap;
    
    vec_assert_valid(v);
    return v;
}

void vec_destroy(t_vec **v) {
    if (!v || !*v) return;
    
    vec_assert_valid(*v);
    mt_free((*v)->data);
    mt_free(*v);
    *v = NULL;
}


void test_invariant_violation(void) {
    printf("\n[DEFENSE TEST 1] Attempting to violate invariant...\n");
    printf("  Manually setting v->size > v->cap\n");
    
    t_vec *v = vec_create(4);
    v->data[0] = 100;
    v->size = 1;
    
    printf("  [ATTACK] Setting size = 10, cap = 4\n");
    v->size = 10;
    
    printf("  [DEFENSE] Calling vec_push() to trigger invariant check...\n");
    vec_push(v, 999);
}

void test_double_free(void) {
    printf("\n[DEFENSE TEST 2] Attempting double free...\n");
    
    int *ptr = (int *)mt_malloc(sizeof(int) * 10);
    *ptr = 42;
    printf("  Allocated memory at %p\n", ptr);
    
    printf("  [ATTACK] First free...\n");
    mt_free(ptr);
    printf("  ✓ First free succeeded\n");
    
    printf("  [ATTACK] Attempting second free of same pointer...\n");
    mt_free(ptr);
}

void test_overflow_protection(void) {
    printf("\n[DEFENSE TEST 3] Integer overflow protection...\n");
    
    t_vec *v = vec_create(2);
    
    printf("  Manually setting capacity to near limit: %d\n", (1 << 30) + 1);
    v->cap = (1 << 30) + 1;
    v->size = (1 << 30);
    
    printf("  [DEFENSE] Attempting to push when cap overflow would occur...\n");
    int ret = vec_push(v, 999);
    
    if (ret == -1) {
        printf("  ✓ Overflow detected, push returned -1\n");
    }
}

int main(int argc, char *argv[]) {
    printf("===== SYSTEM DEFENSE DEMONSTRATION =====\n");
    printf("\nUsage: test_defense [1|2|3|normal]\n");
    printf("  1 = Invariant violation attack\n");
    printf("  2 = Double free attack\n");
    printf("  3 = Integer overflow attack\n");
    printf("  normal = Normal safe operation (default)\n\n");
    
    if (argc < 2) {
        printf("[Running normal safe operation]\n");
        goto normal_test;
    }
    
    if (argv[1][0] == '1') {
        test_invariant_violation();
    } else if (argv[1][0] == '2') {
        test_double_free();
    } else if (argv[1][0] == '3') {
        test_overflow_protection();
    } else {
        goto normal_test;
    }
    
    printf("\n[If you see this, the attack was NOT fully blocked]\n");
    return 0;

normal_test:
    printf("[TEST: Safe vector operations]\n");
    t_vec *v = vec_create(2);
    
    for (int i = 0; i < 10; i++) {
        vec_push(v, i * 100);
    }
    printf("  Pushed 10 values successfully\n");
    
    vec_destroy(&v);
    printf("  ✓ Memory freed safely\n");
    printf("  ✓ Active allocations: %d (expected 0)\n", g_count);
    
    if (g_count == 0) {
        printf("\n===== DEFENSE SYSTEM: ALL CHECKS PASSED =====\n");
    }
    
    return 0;
}
