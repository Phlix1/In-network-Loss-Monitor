#include <omp.h>
#include <iostream>
#include <map>
#include <string>
#include<fstream>
#include <sys/time.h>    
#include "Graph.h"
using namespace std;
#define THREAD_NUM 8
#define MAX_LENGTH 3

int total_pathnum = 0;
int selpath_num = 0;
string total_paths[1000000][MAX_LENGTH];
string thread_paths[THREAD_NUM][1000000][MAX_LENGTH];
int thread_pnum[THREAD_NUM];
string sorted_total_paths[1000000][MAX_LENGTH];
string sel_paths[1000000][MAX_LENGTH];
string no_sel[1000000][MAX_LENGTH];

int get_path_len(string *path){
	int len = 0;
	for (int i = 0; i < MAX_LENGTH; i++){
		if (path[i] == ""){
			return len;
		}
		len++;
	}
	return len;
}

void sort_path(){
	int path_len = MAX_LENGTH;
	int path_num = 0;
	while (path_len>0){
		int i = 0;
		while (i < total_pathnum){
			if (get_path_len(total_paths[i]) == path_len){
				for (int j = 0; j < MAX_LENGTH; j++){
					sorted_total_paths[path_num][j] = total_paths[i][j];
				}
				path_num++;
			}
			i++;
		}
		path_len--;
	}
	return;
}


bool is_dst(int n, map<string, int> &vert, string Vs[], int dstnum){
	for (int i = 0; i < dstnum; i++){
		if (n == vert[Vs[i]]){
			return true;
		}
	}
    return false;
}

int DFS_all(Graph<int> &G, string u, string Vs[], string *path, int &d, map<string, int> &vert, map<int, string> &vert1, int &flag, int dstnum) {
	int n = vert[u];
	int v1 = vert[Vs[0]];
	G.setMark(n, 1);
	path[d] = u;
	if (d + 1 > MAX_LENGTH){
		G.setMark(n, 0);
		return flag;
	}
	d++;
	bool isdst = is_dst(n, vert, Vs, dstnum);
	if (isdst&&d >= 1) {
		int threadid = omp_get_thread_num();
		for (int i = 0; i < d; i++){
			//cout<<threadid<<" "<<thread_pnum[threadid]<<" "<<i<<endl;
			thread_paths[threadid][thread_pnum[threadid]][i] = path[i];
			//total_paths[total_pathnum][i] = path[i];
		}
		thread_pnum[threadid]++;
		//total_pathnum++;
		flag++;
		/*
		cout << "path" << flag << ": ";
		for (int i = 0; i<d - 1; i++)
			cout << path[i] << "-->";
		cout << path[d - 1] << endl;
		*/
	}
	for (int w = G.first(n); w<G.n(); w = G.next(n, w)) {
		if (G.getMark(w) == 0)
			DFS_all(G, vert1[w], Vs, path, d, vert, vert1, flag, dstnum);
	}
	G.setMark(n, 0);
	d--;
	return flag;
}
void find_all(Graph<int> &G, string u, string Vs[], map<string, int> vert, map<int, string> vert1, int dstnum) {
	string path[100];
	int d = 0;
	int flag = 0;
	for (int i = 0; i<G.n(); i++)G.setMark(i, 0);
	int temp = DFS_all(G, u, Vs, path, d, vert, vert1, flag, dstnum);
	if (temp == 0)cout << "no path" << endl;
}
bool is_no_overlap(int **EdgeMark, string *path, map<string, int> vert){

	for (int i = 1; i < MAX_LENGTH; i++){
		string a = path[i];
		string b = path[i - 1];
		if (a != "" && b != ""){
			if (EdgeMark[vert[a]][vert[b]] == 1 || EdgeMark[vert[b]][vert[a]] == 1){
				return false;
			}
		}
	}
	return true;
}
void select_path(int **EdgeMark, string *path, map<string, int> vert){
	for (int i = 0; i < MAX_LENGTH; i++){
		if (i > 0){
			string a = path[i];
			string b = path[i - 1];
			if (a != "" && b != ""){
				EdgeMark[vert[a]][vert[b]]++;
				EdgeMark[vert[b]][vert[a]]++;
			}
		}
		sel_paths[selpath_num][i] = path[i];
	}
	selpath_num++;
}
bool has_newedge(int **EdgeMark, string *path, map<string, int> vert){
	for (int i = 1; i < MAX_LENGTH; i++){
		string a = path[i];
		string b = path[i - 1];
		if (a != "" && b != ""){
			if (EdgeMark[vert[a]][vert[b]] == 0 && EdgeMark[vert[b]][vert[a]] == 0){
				return true;
			}
		}
	}
	return false;
}
void select_probe_paths(Graph<int> &G, int n, map<string, int> vert, map<int, string> vert1){
    struct timeval timeStart, timeSort, timeFirst, timeSecond;
	int no_selnum = 0;
	int path_num = 0;
	int **EdgeMark;
	EdgeMark = new int*[n];
	for (int i = 0; i<n; i++) EdgeMark[i] = new int[n];
	for (int i = 0; i<n; i++)
		for (int j = 0; j<n; j++)
			EdgeMark[i][j] = 0;
	// sort path according length
	gettimeofday(&timeStart, NULL);
	sort_path();
	gettimeofday(&timeSort, NULL);
	double Sorttime = (timeSort.tv_sec - timeStart.tv_sec ) + (double)(timeSort.tv_usec -timeStart.tv_usec)/1000000;
	cout << "Sort Time Cost: " << Sorttime << endl;
    // first select
	while (path_num < total_pathnum){
		bool sel_flag = is_no_overlap(EdgeMark, sorted_total_paths[path_num], vert);
		if (sel_flag){
			select_path(EdgeMark, sorted_total_paths[path_num], vert);
		}
		else{
			for (int i = 0; i < MAX_LENGTH; i++){
				no_sel[no_selnum][i] = sorted_total_paths[path_num][i];
			}
			no_selnum++;
		}
		path_num++;
	}
	gettimeofday(&timeFirst, NULL);
	double FirstTime = (timeFirst.tv_sec - timeSort.tv_sec ) + (double)(timeFirst.tv_usec -timeSort.tv_usec)/1000000;
	cout << "First Select Time Cost: " << FirstTime << endl;
	path_num = 0;
	// second choose Note: for fattree and VL2 we do need to second selection
	/*
	while (path_num < no_selnum){
		bool sel_flag = has_newedge(EdgeMark, no_sel[path_num], vert);
		if (sel_flag){
			select_path(EdgeMark, no_sel[path_num], vert);
		}
		path_num++;
	}
	gettimeofday(&timeSecond, NULL);
	*/
	double SecondTime = (timeSecond.tv_sec - timeFirst.tv_sec ) + (double)(timeSecond.tv_usec -timeFirst.tv_usec)/1000000;
	//cout << "Second Select Time Cost: " << SecondTime << endl;
	
	// evaluate
	int wrong_edge = 0;
	int no_probe_number = 0;
	int probe_times[100];
	int max_times = 0;
	for (int i=0; i<100; i++){
		probe_times[i] = 0;
	}
	for (int i=0; i<n-1; i++){
		for (int j=i+1; j<n; j++){
			if (G.isEdge(i,j) && EdgeMark[i][j]==0 && vert1[i][0]!='h' && vert1[j][0]!='h'){
				no_probe_number++;
			}
			else if (G.isEdge(i,j) && EdgeMark[i][j]>0){
				probe_times[EdgeMark[i][j]]++;
				if (EdgeMark[i][j]>max_times){
					max_times = EdgeMark[i][j];
				}
			}
			else if (!G.isEdge(i,j) && EdgeMark[i][j]>0){
				wrong_edge++;
			}
		}
	}
    cout << "Algorithm Evaluation:" << endl;
	cout << "Wrong Edges: " << wrong_edge << endl;
	cout << "No Probe Edge Number: " << no_probe_number << endl;
	for (int i=0;i<max_times;i++){
		cout << "Probe " << i+1 << " times Edge number: " << probe_times[i+1] << endl;
	}
	return;
}

int main() {
	struct timeval timeStart, timeEnd, timeSystemStart, timeStep1, timeStep2;
	double runTime=0;
	
	for(int i=0; i<THREAD_NUM; i++){
		thread_pnum[i]=0;
	}
	map<string, int> vert;
	map<int, string> vert1;
	ifstream inFIle;
	char filename[100];
	int thread_num = 1;
	cout << "Network File:" << endl;
	cin >> filename;
	cout << "Thread num: " << endl;
	cin >> thread_num;
	inFIle.open(filename);
	
	int n;
	inFIle >> n;
	Graph<int> *gs = new Graph<int>[THREAD_NUM];
	for(int i=0; i<THREAD_NUM; i++){
        gs[i].initial(n);
	}
	string a, b;
	for (int i = 0; i<n; i++) {
		inFIle >> a;
		vert[a] = i;
		vert1[i] = a;
	}
	
	while (inFIle >> a && a != "#") {
		inFIle >> b;
		for(int i=0; i<thread_num; i++){
		    gs[i].setEdge(vert[a], vert[b], 1);
		    gs[i].setEdge(vert[b], vert[a], 1);
	    }
	}
	
	int srcnum;
	string src[1000];
	inFIle >> srcnum;
	int c = 0;
	while (c < srcnum){
		inFIle >> src[c];
		c++;
	}
	c = 0;
	int dstnum;
	string dst[2000];
	inFIle >> dstnum;
	while (c < dstnum){
		inFIle >> dst[c];
		c++;
	}
	
	//step 1: find all the path from source switches to sink switches
	gettimeofday(&timeStart, NULL );
	c = 0;
	#pragma omp parallel for num_threads(thread_num)
	for (c=0; c < srcnum; c++){
		int threadid = omp_get_thread_num();
		find_all(gs[threadid], src[c], dst, vert, vert1, dstnum);
	}
	
	for(int i=0; i<thread_num; i++){
		for(int j=0; j<thread_pnum[i]; j++){
			for (int k = 0; k < MAX_LENGTH; k++){
			    total_paths[total_pathnum][k] = thread_paths[i][j][k];
		    }
			total_pathnum++;
		}
	}
	
    gettimeofday(&timeStep1, NULL);
	double Step1runTime = (timeStep1.tv_sec - timeStart.tv_sec ) + (double)(timeStep1.tv_usec -timeStart.tv_usec)/1000000;
	cout << "Find all paths Time Cost: " << Step1runTime <<endl;
	cout << "Total " << total_pathnum << " Paths:" << endl;
	cout << "*********************" << endl;
	
	//int pathnum = 0;
	//while (pathnum < total_pathnum){
	//	for (int i = 0; i < MAX_LENGTH; i++){
	//		cout << total_paths[pathnum][i] << " ";
	//	}
	//	cout << endl;
	//	pathnum++;
	//}
	
    //step 2: select probe paths from all the paths
	select_probe_paths(gs[0], n, vert, vert1);
	gettimeofday(&timeStep2, NULL);
	double Step2runTime = (timeStep2.tv_sec - timeStep1.tv_sec ) + (double)(timeStep2.tv_usec -timeStep1.tv_usec)/1000000;
	cout << "Select paths Time Cost: " << Step2runTime <<endl;
	cout << "Select " << selpath_num << " Paths : " << endl;
	cout << "*********************" << endl;
	
	//int selnum = 0;
	//while (selnum < selpath_num){
	//	for (int i = 0; i < MAX_LENGTH; i++){
	//		cout << sel_paths[selnum][i] << " ";
	//	}
	//	cout << endl;
	//	selnum++;
	//}
	gettimeofday( &timeEnd, NULL ); 
	runTime = (timeEnd.tv_sec - timeStart.tv_sec ) + (double)(timeEnd.tv_usec -timeStart.tv_usec)/1000000;
	cout << "Algorithm Runtime:" << runTime << "s"<<endl;
	
	return 0;
}
