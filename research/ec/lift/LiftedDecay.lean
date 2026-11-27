import Std.Tactic.BVDecide
set_option warningAsError true
set_option maxRecDepth 8192
set_option maxHeartbeats 16000000
namespace R17Decay
def lifted (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16) : BitVec 16 :=
  (let _v1 : BitVec 16 := (r0 &&& (65280 : BitVec 16)); (let _v2 : BitVec 8 := stage; (let _v3 : BitVec 16 := (BitVec.setWidth 16 _v2); (let _v4 : BitVec 16 := (_v1 + _v3); (let _v5 : BitVec 16 := (psr &&& (65471 : BitVec 16)); (let _v6 : BitVec 8 := (if ((11 : BitVec 8) == (BitVec.setWidth 8 _v4)) then (1 : BitVec 8) else 0); (let _v7 : BitVec 16 := (BitVec.setWidth 16 _v6); (let _v8 : BitVec 16 := (BitVec.shiftLeft _v7 6); (let _v9 : BitVec 16 := (_v5 ||| _v8); (let _v10 : BitVec 16 := (_v9 &&& (65407 : BitVec 16)); (let _v11 : BitVec 8 := (if (BitVec.slt (BitVec.setWidth 8 _v4) (11 : BitVec 8)) then (1 : BitVec 8) else 0); (let _v12 : BitVec 16 := (BitVec.setWidth 16 _v11); (let _v13 : BitVec 16 := (BitVec.shiftLeft _v12 7); (let _v14 : BitVec 16 := (_v10 ||| _v13); (let _v15 : BitVec 16 := (_v14 &&& (65531 : BitVec 16)); (let _v16 : BitVec 8 := (if (BitVec.ult (BitVec.setWidth 8 _v4) (11 : BitVec 8)) then (1 : BitVec 8) else 0); (let _v17 : BitVec 16 := (BitVec.setWidth 16 _v16); (let _v18 : BitVec 16 := (BitVec.shiftLeft _v17 2); (let _v19 : BitVec 16 := (_v15 ||| _v18); (let _v20 : BitVec 16 := (BitVec.ushiftRight _v19 6); (let _v21 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v20 0)); (let _v22 : BitVec 8 := (_v21 &&& (1 : BitVec 8)); (let _v23 : BitVec 8 := (if (!(_v22 != 0)) then (1 : BitVec 8) else 0); (let _v24 : BitVec 8 := (if (!(_v23 != 0)) then (1 : BitVec 8) else 0); (if (_v24 != 0) then (let _v25 : BitVec 16 := (_v4 &&& (65280 : BitVec 16)); (let _v26 : BitVec 8 := sub; (let _v27 : BitVec 16 := (BitVec.setWidth 16 _v26); (let _v28 : BitVec 16 := (_v25 + _v27); (let _v29 : BitVec 16 := (_v19 &&& (65471 : BitVec 16)); (let _v30 : BitVec 8 := (if ((0 : BitVec 8) == (BitVec.setWidth 8 _v28)) then (1 : BitVec 8) else 0); (let _v31 : BitVec 16 := (BitVec.setWidth 16 _v30); (let _v32 : BitVec 16 := (BitVec.shiftLeft _v31 6); (let _v33 : BitVec 16 := (_v29 ||| _v32); (let _v34 : BitVec 16 := (_v33 &&& (65407 : BitVec 16)); (let _v35 : BitVec 8 := (if (BitVec.slt (BitVec.setWidth 8 _v28) (0 : BitVec 8)) then (1 : BitVec 8) else 0); (let _v36 : BitVec 16 := (BitVec.setWidth 16 _v35); (let _v37 : BitVec 16 := (BitVec.shiftLeft _v36 7); (let _v38 : BitVec 16 := (_v34 ||| _v37); (let _v39 : BitVec 16 := (_v38 &&& (65531 : BitVec 16)); (let _v40 : BitVec 8 := (if (BitVec.ult (BitVec.setWidth 8 _v28) (0 : BitVec 8)) then (1 : BitVec 8) else 0); (let _v41 : BitVec 16 := (BitVec.setWidth 16 _v40); (let _v42 : BitVec 16 := (BitVec.shiftLeft _v41 2); (let _v43 : BitVec 16 := (_v39 ||| _v42); (let _v44 : BitVec 16 := (BitVec.ushiftRight _v43 6); (let _v45 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v44 0)); (let _v46 : BitVec 8 := (_v45 &&& (1 : BitVec 8)); (let _v47 : BitVec 8 := (if (!(_v46 != 0)) then (1 : BitVec 8) else 0); (let _v48 : BitVec 8 := (if (!(_v47 != 0)) then (1 : BitVec 8) else 0); (if (_v48 != 0) then (let _v49 : BitVec 16 := (_v28 &&& (65280 : BitVec 16)); (let _v50 : BitVec 8 := misses; (let _v51 : BitVec 16 := (BitVec.setWidth 16 _v50); (let _v52 : BitVec 16 := (_v49 + _v51); (let _v53 : BitVec 16 := (_v43 &&& (65471 : BitVec 16)); (let _v54 : BitVec 8 := (if ((0 : BitVec 8) == (BitVec.setWidth 8 _v52)) then (1 : BitVec 8) else 0); (let _v55 : BitVec 16 := (BitVec.setWidth 16 _v54); (let _v56 : BitVec 16 := (BitVec.shiftLeft _v55 6); (let _v57 : BitVec 16 := (_v53 ||| _v56); (let _v58 : BitVec 16 := (_v57 &&& (65407 : BitVec 16)); (let _v59 : BitVec 8 := (if (BitVec.slt (BitVec.setWidth 8 _v52) (0 : BitVec 8)) then (1 : BitVec 8) else 0); (let _v60 : BitVec 16 := (BitVec.setWidth 16 _v59); (let _v61 : BitVec 16 := (BitVec.shiftLeft _v60 7); (let _v62 : BitVec 16 := (_v58 ||| _v61); (let _v63 : BitVec 16 := (_v62 &&& (65531 : BitVec 16)); (let _v64 : BitVec 8 := (if (BitVec.ult (BitVec.setWidth 8 _v52) (0 : BitVec 8)) then (1 : BitVec 8) else 0); (let _v65 : BitVec 16 := (BitVec.setWidth 16 _v64); (let _v66 : BitVec 16 := (BitVec.shiftLeft _v65 2); (let _v67 : BitVec 16 := (_v63 ||| _v66); (let _v68 : BitVec 16 := (BitVec.ushiftRight _v67 6); (let _v69 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v68 0)); (let _v70 : BitVec 8 := (_v69 &&& (1 : BitVec 8)); (let _v71 : BitVec 8 := (if (!(_v70 != 0)) then (1 : BitVec 8) else 0); (let _v72 : BitVec 8 := (if (!(_v71 != 0)) then (1 : BitVec 8) else 0); (if (_v72 != 0) then (let _v73 : BitVec 16 := upper; (let _v74 : BitVec 16 := (_v67 &&& (65471 : BitVec 16)); (let _v75 : BitVec 8 := (if ((500 : BitVec 16) == _v73) then (1 : BitVec 8) else 0); (let _v76 : BitVec 16 := (BitVec.setWidth 16 _v75); (let _v77 : BitVec 16 := (BitVec.shiftLeft _v76 6); (let _v78 : BitVec 16 := (_v74 ||| _v77); (let _v79 : BitVec 16 := (_v78 &&& (65407 : BitVec 16)); (let _v80 : BitVec 8 := (if (BitVec.slt _v73 (500 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v81 : BitVec 16 := (BitVec.setWidth 16 _v80); (let _v82 : BitVec 16 := (BitVec.shiftLeft _v81 7); (let _v83 : BitVec 16 := (_v79 ||| _v82); (let _v84 : BitVec 16 := (_v83 &&& (65531 : BitVec 16)); (let _v85 : BitVec 8 := (if (BitVec.ult _v73 (500 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v86 : BitVec 16 := (BitVec.setWidth 16 _v85); (let _v87 : BitVec 16 := (BitVec.shiftLeft _v86 2); (let _v88 : BitVec 16 := (_v84 ||| _v87); (let _v89 : BitVec 16 := (BitVec.ushiftRight _v88 6); (let _v90 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v89 0)); (let _v91 : BitVec 8 := (_v90 &&& (1 : BitVec 8)); (let _v92 : BitVec 8 := (if (!(_v91 != 0)) then (1 : BitVec 8) else 0); (let _v93 : BitVec 8 := (if (!(_v92 != 0)) then (1 : BitVec 8) else 0); (if (_v93 != 0) then (let _v94 : BitVec 16 := lower; (let _v95 : BitVec 16 := (_v88 &&& (65471 : BitVec 16)); (let _v96 : BitVec 8 := (if ((25 : BitVec 16) == _v94) then (1 : BitVec 8) else 0); (let _v97 : BitVec 16 := (BitVec.setWidth 16 _v96); (let _v98 : BitVec 16 := (BitVec.shiftLeft _v97 6); (let _v99 : BitVec 16 := (_v95 ||| _v98); (let _v100 : BitVec 16 := (_v99 &&& (65407 : BitVec 16)); (let _v101 : BitVec 8 := (if (BitVec.slt _v94 (25 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v102 : BitVec 16 := (BitVec.setWidth 16 _v101); (let _v103 : BitVec 16 := (BitVec.shiftLeft _v102 7); (let _v104 : BitVec 16 := (_v100 ||| _v103); (let _v105 : BitVec 16 := (_v104 &&& (65531 : BitVec 16)); (let _v106 : BitVec 8 := (if (BitVec.ult _v94 (25 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v107 : BitVec 16 := (BitVec.setWidth 16 _v106); (let _v108 : BitVec 16 := (BitVec.shiftLeft _v107 2); (let _v109 : BitVec 16 := (_v105 ||| _v108); (let _v110 : BitVec 16 := (BitVec.ushiftRight _v109 6); (let _v111 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v110 0)); (let _v112 : BitVec 8 := (_v111 &&& (1 : BitVec 8)); (let _v113 : BitVec 16 := (BitVec.ushiftRight _v109 2); (let _v114 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v113 0)); (let _v115 : BitVec 8 := (_v114 &&& (1 : BitVec 8)); (let _v116 : BitVec 8 := (if ((_v112 != 0) || (_v115 != 0)) then (1 : BitVec 8) else 0); (let _v117 : BitVec 8 := (if (!(_v116 != 0)) then (1 : BitVec 8) else 0); (if (_v117 != 0) then (let _v118 : BitVec 16 := (_v109 &&& (65471 : BitVec 16)); (let _v119 : BitVec 8 := (if ((500 : BitVec 16) == _v94) then (1 : BitVec 8) else 0); (let _v120 : BitVec 16 := (BitVec.setWidth 16 _v119); (let _v121 : BitVec 16 := (BitVec.shiftLeft _v120 6); (let _v122 : BitVec 16 := (_v118 ||| _v121); (let _v123 : BitVec 16 := (_v122 &&& (65407 : BitVec 16)); (let _v124 : BitVec 8 := (if (BitVec.slt _v94 (500 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v125 : BitVec 16 := (BitVec.setWidth 16 _v124); (let _v126 : BitVec 16 := (BitVec.shiftLeft _v125 7); (let _v127 : BitVec 16 := (_v123 ||| _v126); (let _v128 : BitVec 16 := (_v127 &&& (65531 : BitVec 16)); (let _v129 : BitVec 8 := (if (BitVec.ult _v94 (500 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v130 : BitVec 16 := (BitVec.setWidth 16 _v129); (let _v131 : BitVec 16 := (BitVec.shiftLeft _v130 2); (let _v132 : BitVec 16 := (_v128 ||| _v131); (let _v133 : BitVec 16 := (BitVec.ushiftRight _v132 6); (let _v134 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v133 0)); (let _v135 : BitVec 8 := (_v134 &&& (1 : BitVec 8)); (let _v136 : BitVec 8 := (if (!(_v135 != 0)) then (1 : BitVec 8) else 0); (let _v137 : BitVec 16 := (BitVec.ushiftRight _v132 2); (let _v138 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v137 0)); (let _v139 : BitVec 8 := (_v138 &&& (1 : BitVec 8)); (let _v140 : BitVec 8 := (if (!(_v139 != 0)) then (1 : BitVec 8) else 0); (let _v141 : BitVec 8 := (if ((_v136 != 0) && (_v140 != 0)) then (1 : BitVec 8) else 0); (let _v142 : BitVec 8 := (if (!(_v141 != 0)) then (1 : BitVec 8) else 0); (if (_v142 != 0) then (let _v143 : BitVec 16 := output; (let _v144 : BitVec 16 := (_v132 &&& (65471 : BitVec 16)); (let _v145 : BitVec 8 := (if (_v94 == _v143) then (1 : BitVec 8) else 0); (let _v146 : BitVec 16 := (BitVec.setWidth 16 _v145); (let _v147 : BitVec 16 := (BitVec.shiftLeft _v146 6); (let _v148 : BitVec 16 := (_v144 ||| _v147); (let _v149 : BitVec 16 := (_v148 &&& (65407 : BitVec 16)); (let _v150 : BitVec 8 := (if (BitVec.slt _v143 _v94) then (1 : BitVec 8) else 0); (let _v151 : BitVec 16 := (BitVec.setWidth 16 _v150); (let _v152 : BitVec 16 := (BitVec.shiftLeft _v151 7); (let _v153 : BitVec 16 := (_v149 ||| _v152); (let _v154 : BitVec 16 := (_v153 &&& (65531 : BitVec 16)); (let _v155 : BitVec 8 := (if (BitVec.ult _v143 _v94) then (1 : BitVec 8) else 0); (let _v156 : BitVec 16 := (BitVec.setWidth 16 _v155); (let _v157 : BitVec 16 := (BitVec.shiftLeft _v156 2); (let _v158 : BitVec 16 := (_v154 ||| _v157); (let _v159 : BitVec 16 := (BitVec.ushiftRight _v158 6); (let _v160 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v159 0)); (let _v161 : BitVec 8 := (_v160 &&& (1 : BitVec 8)); (let _v162 : BitVec 8 := (if (!(_v161 != 0)) then (1 : BitVec 8) else 0); (let _v163 : BitVec 8 := (if (!(_v162 != 0)) then (1 : BitVec 8) else 0); (if (_v163 != 0) then (let _v164 : BitVec 16 := (_v158 &&& (65471 : BitVec 16)); (let _v165 : BitVec 8 := (if (_v94 == request) then (1 : BitVec 8) else 0); (let _v166 : BitVec 16 := (BitVec.setWidth 16 _v165); (let _v167 : BitVec 16 := (BitVec.shiftLeft _v166 6); (let _v168 : BitVec 16 := (_v164 ||| _v167); (let _v169 : BitVec 16 := (_v168 &&& (65407 : BitVec 16)); (let _v170 : BitVec 8 := (if (BitVec.slt request _v94) then (1 : BitVec 8) else 0); (let _v171 : BitVec 16 := (BitVec.setWidth 16 _v170); (let _v172 : BitVec 16 := (BitVec.shiftLeft _v171 7); (let _v173 : BitVec 16 := (_v169 ||| _v172); (let _v174 : BitVec 16 := (_v173 &&& (65531 : BitVec 16)); (let _v175 : BitVec 8 := (if (BitVec.ult request _v94) then (1 : BitVec 8) else 0); (let _v176 : BitVec 16 := (BitVec.setWidth 16 _v175); (let _v177 : BitVec 16 := (BitVec.shiftLeft _v176 2); (let _v178 : BitVec 16 := (_v174 ||| _v177); (let _v179 : BitVec 16 := (BitVec.ushiftRight _v178 2); (let _v180 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v179 0)); (let _v181 : BitVec 8 := (_v180 &&& (1 : BitVec 8)); (let _v182 : BitVec 8 := (if (!(_v181 != 0)) then (1 : BitVec 8) else 0); (let _v183 : BitVec 8 := (if (!(_v182 != 0)) then (1 : BitVec 8) else 0); (if (_v183 != 0) then (let _v184 : BitVec 16 := target; (let _v185 : BitVec 16 := (_v178 &&& (65471 : BitVec 16)); (let _v186 : BitVec 8 := (if ((0 : BitVec 16) == _v184) then (1 : BitVec 8) else 0); (let _v187 : BitVec 16 := (BitVec.setWidth 16 _v186); (let _v188 : BitVec 16 := (BitVec.shiftLeft _v187 6); (let _v189 : BitVec 16 := (_v185 ||| _v188); (let _v190 : BitVec 16 := (_v189 &&& (65407 : BitVec 16)); (let _v191 : BitVec 8 := (if (BitVec.slt _v184 (0 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v192 : BitVec 16 := (BitVec.setWidth 16 _v191); (let _v193 : BitVec 16 := (BitVec.shiftLeft _v192 7); (let _v194 : BitVec 16 := (_v190 ||| _v193); (let _v195 : BitVec 16 := (_v194 &&& (65531 : BitVec 16)); (let _v196 : BitVec 8 := (if (BitVec.ult _v184 (0 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v197 : BitVec 16 := (BitVec.setWidth 16 _v196); (let _v198 : BitVec 16 := (BitVec.shiftLeft _v197 2); (let _v199 : BitVec 16 := (_v195 ||| _v198); (let _v200 : BitVec 16 := (BitVec.ushiftRight _v199 6); (let _v201 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v200 0)); (let _v202 : BitVec 8 := (_v201 &&& (1 : BitVec 8)); (let _v203 : BitVec 8 := (if (!(_v202 != 0)) then (1 : BitVec 8) else 0); (if (_v203 != 0) then (let _v204 : BitVec 16 := (_v199 &&& (65471 : BitVec 16)); (let _v205 : BitVec 8 := (if ((10000 : BitVec 16) == _v184) then (1 : BitVec 8) else 0); (let _v206 : BitVec 16 := (BitVec.setWidth 16 _v205); (let _v207 : BitVec 16 := (BitVec.shiftLeft _v206 6); (let _v208 : BitVec 16 := (_v204 ||| _v207); (let _v209 : BitVec 16 := (_v208 &&& (65407 : BitVec 16)); (let _v210 : BitVec 8 := (if (BitVec.slt _v184 (10000 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v211 : BitVec 16 := (BitVec.setWidth 16 _v210); (let _v212 : BitVec 16 := (BitVec.shiftLeft _v211 7); (let _v213 : BitVec 16 := (_v209 ||| _v212); (let _v214 : BitVec 16 := (_v213 &&& (65531 : BitVec 16)); (let _v215 : BitVec 8 := (if (BitVec.ult _v184 (10000 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v216 : BitVec 16 := (BitVec.setWidth 16 _v215); (let _v217 : BitVec 16 := (BitVec.shiftLeft _v216 2); (let _v218 : BitVec 16 := (_v214 ||| _v217); (let _v219 : BitVec 16 := (BitVec.ushiftRight _v218 6); (let _v220 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v219 0)); (let _v221 : BitVec 8 := (_v220 &&& (1 : BitVec 8)); (let _v222 : BitVec 8 := (if (!(_v221 != 0)) then (1 : BitVec 8) else 0); (let _v223 : BitVec 16 := (BitVec.ushiftRight _v218 2); (let _v224 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v223 0)); (let _v225 : BitVec 8 := (_v224 &&& (1 : BitVec 8)); (let _v226 : BitVec 8 := (if (!(_v225 != 0)) then (1 : BitVec 8) else 0); (let _v227 : BitVec 8 := (if ((_v222 != 0) && (_v226 != 0)) then (1 : BitVec 8) else 0); (let _v228 : BitVec 8 := (if (!(_v227 != 0)) then (1 : BitVec 8) else 0); (if (_v228 != 0) then (let _v229 : BitVec 16 := (_v218 &&& (65534 : BitVec 16)); (let _v230 : BitVec 8 := (if (BitVec.ult ((100 : BitVec 16) + _v184) (100 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v231 : BitVec 16 := (BitVec.setWidth 16 _v230); (let _v232 : BitVec 16 := (_v229 ||| _v231); (let _v233 : BitVec 16 := (_v232 &&& (65503 : BitVec 16)); (let _v234 : BitVec 8 := (if (((BitVec.slt (100 : BitVec 16) 0) == (BitVec.slt _v184 0)) && ((BitVec.slt (100 : BitVec 16) 0) != (BitVec.slt ((100 : BitVec 16) + _v184) 0))) then (1 : BitVec 8) else 0); (let _v235 : BitVec 16 := (BitVec.setWidth 16 _v234); (let _v236 : BitVec 16 := (BitVec.shiftLeft _v235 5); (let _v237 : BitVec 16 := (_v233 ||| _v236); (let _v238 : BitVec 16 := (_v184 + (100 : BitVec 16)); (let _v239 : BitVec 16 := rpm; (let _v240 : BitVec 16 := (_v237 &&& (65471 : BitVec 16)); (let _v241 : BitVec 8 := (if ((65535 : BitVec 16) == _v239) then (1 : BitVec 8) else 0); (let _v242 : BitVec 16 := (BitVec.setWidth 16 _v241); (let _v243 : BitVec 16 := (BitVec.shiftLeft _v242 6); (let _v244 : BitVec 16 := (_v240 ||| _v243); (let _v245 : BitVec 16 := (_v244 &&& (65407 : BitVec 16)); (let _v246 : BitVec 8 := (if (BitVec.slt _v239 (65535 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v247 : BitVec 16 := (BitVec.setWidth 16 _v246); (let _v248 : BitVec 16 := (BitVec.shiftLeft _v247 7); (let _v249 : BitVec 16 := (_v245 ||| _v248); (let _v250 : BitVec 16 := (_v249 &&& (65531 : BitVec 16)); (let _v251 : BitVec 8 := (if (BitVec.ult _v239 (65535 : BitVec 16)) then (1 : BitVec 8) else 0); (let _v252 : BitVec 16 := (BitVec.setWidth 16 _v251); (let _v253 : BitVec 16 := (BitVec.shiftLeft _v252 2); (let _v254 : BitVec 16 := (_v250 ||| _v253); (let _v255 : BitVec 16 := (BitVec.ushiftRight _v254 6); (let _v256 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v255 0)); (let _v257 : BitVec 8 := (_v256 &&& (1 : BitVec 8)); (let _v258 : BitVec 8 := (if (!(_v257 != 0)) then (1 : BitVec 8) else 0); (if (_v258 != 0) then (let _v259 : BitVec 16 := (_v254 &&& (65471 : BitVec 16)); (let _v260 : BitVec 8 := (if (_v238 == _v239) then (1 : BitVec 8) else 0); (let _v261 : BitVec 16 := (BitVec.setWidth 16 _v260); (let _v262 : BitVec 16 := (BitVec.shiftLeft _v261 6); (let _v263 : BitVec 16 := (_v259 ||| _v262); (let _v264 : BitVec 16 := (_v263 &&& (65407 : BitVec 16)); (let _v265 : BitVec 8 := (if (BitVec.slt _v239 _v238) then (1 : BitVec 8) else 0); (let _v266 : BitVec 16 := (BitVec.setWidth 16 _v265); (let _v267 : BitVec 16 := (BitVec.shiftLeft _v266 7); (let _v268 : BitVec 16 := (_v264 ||| _v267); (let _v269 : BitVec 16 := (_v268 &&& (65531 : BitVec 16)); (let _v270 : BitVec 8 := (if (BitVec.ult _v239 _v238) then (1 : BitVec 8) else 0); (let _v271 : BitVec 16 := (BitVec.setWidth 16 _v270); (let _v272 : BitVec 16 := (BitVec.shiftLeft _v271 2); (let _v273 : BitVec 16 := (_v269 ||| _v272); (let _v274 : BitVec 16 := (BitVec.ushiftRight _v273 6); (let _v275 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v274 0)); (let _v276 : BitVec 8 := (_v275 &&& (1 : BitVec 8)); (let _v277 : BitVec 16 := (BitVec.ushiftRight _v273 2); (let _v278 : BitVec 8 := (BitVec.setWidth 8 (BitVec.ushiftRight _v277 0)); (let _v279 : BitVec 8 := (_v278 &&& (1 : BitVec 8)); (let _v280 : BitVec 8 := (if ((_v276 != 0) || (_v279 != 0)) then (1 : BitVec 8) else 0); (let _v281 : BitVec 8 := (if (!(_v280 != 0)) then (1 : BitVec 8) else 0); (if (_v281 != 0) then (let _v282 : BitVec 16 := (_v273 &&& (65534 : BitVec 16)); (let _v283 : BitVec 8 := (if (BitVec.ult (1 : BitVec 16) _v94) then (1 : BitVec 8) else 0); (let _v284 : BitVec 16 := (BitVec.setWidth 16 _v283); (let _v285 : BitVec 16 := (_v282 ||| _v284); (let _v286 : BitVec 16 := (_v285 &&& (65503 : BitVec 16)); (let _v287 : BitVec 8 := (if (((BitVec.slt (1 : BitVec 16) 0) != (BitVec.slt _v94 0)) && ((BitVec.slt (1 : BitVec 16) 0) != (BitVec.slt ((1 : BitVec 16) - _v94) 0))) then (1 : BitVec 8) else 0); (let _v288 : BitVec 16 := (BitVec.setWidth 16 _v287); (let _v289 : BitVec 16 := (BitVec.shiftLeft _v288 5); (let _v290 : BitVec 16 := (_v286 ||| _v289); (let _v291 : BitVec 16 := (_v94 - (1 : BitVec 16)); _v291)))))))))) else lower)))))))))))))))))))))))) else lower))))))))))))))))))))))))))))))) else lower)))))))))))))))))))))))))) else lower))))))))))))))))))))) else lower))))))))))))))))))))) else lower)))))))))))))))))))))) else lower)))))))))))))))))))))))))) else lower))))))))))))))))))))))))) else lower)))))))))))))))))))))) else lower))))))))))))))))))))))))) else lower))))))))))))))))))))))))) else lower)))))))))))))))))))))))))
def enabled (stage sub misses : BitVec 8)
    (lower upper output request target rpm : BitVec 16) : Prop :=
  stage = 11 ∧ sub = 0 ∧ misses = 0 ∧ upper = 500 ∧
  25 < lower ∧ lower ≤ 500 ∧ output = lower ∧ request < lower ∧
  0 < target ∧ target ≤ 10000 ∧ rpm ≠ 65535 ∧ target + 100 < rpm

def spec (stage sub misses : BitVec 8)
    (lower upper output request target rpm : BitVec 16) : BitVec 16 :=
  if stage = 11 ∧ sub = 0 ∧ misses = 0 ∧ upper = 500 ∧
    25 < lower ∧ lower ≤ 500 ∧ output = lower ∧ request < lower ∧
    0 < target ∧ target ≤ 10000 ∧ rpm ≠ 65535 ∧ target + 100 < rpm
  then lower - 1 else lower

theorem exact_decay (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16) :
    lifted stage sub misses lower upper output request target rpm r0 psr =
    spec stage sub misses lower upper output request target rpm := by
  unfold lifted spec
  bv_decide

theorem missing_feedback (stage sub misses : BitVec 8)
    (lower upper output request target r0 psr : BitVec 16) :
    lifted stage sub misses lower upper output request target 65535 r0 psr = lower := by
  rw [exact_decay]
  simp [spec]

theorem disabled_when_recovering (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : stage ≠ 11 ∨ sub ≠ 0 ∨ misses ≠ 0) :
    lifted stage sub misses lower upper output request target rpm r0 psr = lower := by
  rw [exact_decay]
  unfold spec
  bv_decide

theorem no_underspeed_decay (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : rpm ≤ target) :
    lifted stage sub misses lower upper output request target rpm r0 psr = lower := by
  rw [exact_decay]
  unfold spec
  bv_decide

theorem bounded_step (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : 25 ≤ lower) (h2 : lower ≤ 500) :
    25 ≤ lifted stage sub misses lower upper output request target rpm r0 psr ∧
    (lifted stage sub misses lower upper output request target rpm r0 psr = lower ∨
     lifted stage sub misses lower upper output request target rpm r0 psr = lower - 1) := by
  rw [exact_decay]
  unfold spec
  bv_decide

theorem progress_on_eligible_sample (stage sub misses : BitVec 8)
    (lower upper output request target rpm r0 psr : BitVec 16)
    (h : enabled stage sub misses lower upper output request target rpm) :
    lifted stage sub misses lower upper output request target rpm r0 psr = lower - 1 := by
  rw [exact_decay]
  unfold enabled at h
  unfold spec
  exact if_pos h

-- A single high but non-sentinel value is sufficient; physical validity is external.
theorem high_reading_counterexample : lifted 11 0 0 500 500 500 499 2550 65534 0 0 = 499 := by decide

#print axioms high_reading_counterexample
#print axioms exact_decay
#print axioms missing_feedback
#print axioms disabled_when_recovering
#print axioms no_underspeed_decay
#print axioms bounded_step
#print axioms progress_on_eligible_sample
example : lifted 11 0 0 500 500 500 499 2550 5000 0 0 = 499 := by decide
example : lifted 0 0 0 500 500 500 499 2550 5000 49213 54870 = 500 := by decide
example : lifted 10 0 0 500 500 500 499 2550 5000 28320 63062 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 30218 9623 = 499 := by decide
example : lifted 12 0 0 500 500 500 499 2550 5000 6683 18486 = 500 := by decide
example : lifted 255 0 0 500 500 500 499 2550 5000 2659 37278 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 18139 36810 = 499 := by decide
example : lifted 11 1 0 500 500 500 499 2550 5000 24654 48110 = 500 := by decide
example : lifted 11 255 0 500 500 500 499 2550 5000 951 38892 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 46689 1859 = 499 := by decide
example : lifted 11 0 1 500 500 500 499 2550 5000 57048 52318 = 500 := by decide
example : lifted 11 0 8 500 500 500 499 2550 5000 1298 18608 = 500 := by decide
example : lifted 11 0 9 500 500 500 499 2550 5000 24670 58579 = 500 := by decide
example : lifted 11 0 127 500 500 500 499 2550 5000 17304 44012 = 500 := by decide
example : lifted 11 0 255 500 500 500 499 2550 5000 17006 35085 = 500 := by decide
example : lifted 11 0 0 0 500 0 0 2550 5000 39914 53180 = 0 := by decide
example : lifted 11 0 0 24 500 24 23 2550 5000 14126 840 = 24 := by decide
example : lifted 11 0 0 25 500 25 24 2550 5000 16373 13978 = 25 := by decide
example : lifted 11 0 0 26 500 26 25 2550 5000 5127 12400 = 25 := by decide
example : lifted 11 0 0 499 500 499 498 2550 5000 44518 12962 = 498 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 47636 46181 = 499 := by decide
example : lifted 11 0 0 501 500 501 500 2550 5000 62161 50189 = 501 := by decide
example : lifted 11 0 0 65535 500 65535 65534 2550 5000 37641 18212 = 65535 := by decide
example : lifted 11 0 0 500 0 500 499 2550 5000 2454 44510 = 500 := by decide
example : lifted 11 0 0 500 499 500 499 2550 5000 37153 30504 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 10879 42694 = 499 := by decide
example : lifted 11 0 0 500 501 500 499 2550 5000 15753 333 = 500 := by decide
example : lifted 11 0 0 500 65535 500 499 2550 5000 36389 49944 = 500 := by decide
example : lifted 11 0 0 500 500 0 499 2550 5000 1003 26548 = 500 := by decide
example : lifted 11 0 0 500 500 25 499 2550 5000 20261 25099 = 500 := by decide
example : lifted 11 0 0 500 500 499 499 2550 5000 59654 35669 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 12485 21236 = 499 := by decide
example : lifted 11 0 0 500 500 501 499 2550 5000 40521 2064 = 500 := by decide
example : lifted 11 0 0 500 500 65535 499 2550 5000 51401 63627 = 500 := by decide
example : lifted 11 0 0 500 500 500 0 2550 5000 11056 1123 = 499 := by decide
example : lifted 11 0 0 500 500 500 24 2550 5000 65294 46890 = 499 := by decide
example : lifted 11 0 0 500 500 500 25 2550 5000 32520 9701 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 55747 27024 = 499 := by decide
example : lifted 11 0 0 500 500 500 500 2550 5000 20709 50495 = 500 := by decide
example : lifted 11 0 0 500 500 500 501 2550 5000 59391 17391 = 500 := by decide
example : lifted 11 0 0 500 500 500 65535 2550 5000 63608 12572 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 0 5000 18939 61902 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 1 5000 61167 29317 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 50365 46574 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 9999 5000 35809 16226 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 10000 5000 41628 26437 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 10001 5000 19753 34164 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 65535 5000 29016 47185 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 0 37442 43242 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 299 17702 53705 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 1141 35357 27306 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 2550 50455 56485 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 2649 5617 41729 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 2650 23564 13335 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 2651 23105 4767 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 57629 5262 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 65534 31222 32064 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 65535 32323 21407 = 500 := by decide
example : lifted 11 0 0 500 500 501 501 2550 5000 1435 37100 = 500 := by decide
example : lifted 11 0 127 500 500 500 499 2550 5000 14239 52881 = 500 := by decide
example : lifted 11 0 0 51 500 51 20 7398 8188 2931 22341 = 50 := by decide
example : lifted 12 0 0 500 500 500 499 2550 5000 4963 4369 = 500 := by decide
example : lifted 11 0 0 500 500 25 499 2550 5000 7693 7691 = 500 := by decide
example : lifted 11 0 0 146 500 146 40 1280 2595 52046 48798 = 145 := by decide
example : lifted 11 0 255 500 500 500 499 10000 5000 9076 22437 = 500 := by decide
example : lifted 10 0 0 500 0 0 499 2550 5000 62902 55 = 500 := by decide
example : lifted 11 0 0 416 500 416 311 264 1524 44391 35237 = 415 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 42041 65322 = 499 := by decide
example : lifted 11 255 0 24 500 500 499 2550 5000 57837 19660 = 24 := by decide
example : lifted 11 0 0 456 500 456 352 7052 9729 6343 46068 = 455 := by decide
example : lifted 12 0 8 500 500 0 25 2550 1141 2741 15117 = 500 := by decide
example : lifted 11 0 8 501 500 500 499 2550 5000 14347 33842 = 501 := by decide
example : lifted 11 0 0 358 500 358 207 8689 11098 43570 59354 = 357 := by decide
example : lifted 255 255 0 0 500 500 499 2550 65535 20453 39737 = 0 := by decide
example : lifted 255 1 0 500 499 65535 499 2550 1141 45094 64482 = 500 := by decide
example : lifted 11 0 0 440 500 440 164 9069 11469 693 7047 = 439 := by decide
example : lifted 11 0 0 500 500 500 499 65535 5000 31189 56336 = 500 := by decide
example : lifted 11 0 0 500 500 0 499 65535 65535 49104 62803 = 500 := by decide
example : lifted 11 0 0 340 500 340 164 6418 9364 48799 54547 = 339 := by decide
example : lifted 11 0 0 500 500 500 25 2550 2649 64731 10725 = 500 := by decide
example : lifted 11 255 0 0 500 500 499 2550 5000 5569 30507 = 0 := by decide
example : lifted 11 0 0 297 500 297 114 3710 6785 34926 2504 = 296 := by decide
example : lifted 11 0 1 501 500 500 499 10001 5000 36242 35806 = 501 := by decide
example : lifted 11 1 0 500 500 500 499 2550 5000 24682 39637 = 500 := by decide
example : lifted 11 0 0 404 500 404 43 1482 3801 62459 56593 = 403 := by decide
example : lifted 255 0 0 500 65535 500 499 2550 5000 8783 50439 = 500 := by decide
example : lifted 11 0 0 25 500 500 0 2550 2649 1138 61639 = 25 := by decide
example : lifted 11 0 0 303 500 303 109 3262 5162 38348 55341 = 302 := by decide
example : lifted 0 0 0 500 500 500 499 2550 5000 43193 30629 = 500 := by decide
example : lifted 11 1 0 24 500 500 499 2550 5000 10653 39179 = 24 := by decide
example : lifted 11 0 0 228 500 228 65 5667 7179 40496 34890 = 227 := by decide
example : lifted 11 0 8 65535 500 500 499 2550 5000 47257 5703 = 65535 := by decide
example : lifted 11 0 0 24 500 500 499 2550 5000 62696 61620 = 24 := by decide
example : lifted 11 0 0 341 500 341 142 2439 3742 23364 31535 = 340 := by decide
example : lifted 11 255 0 0 500 0 499 2550 5000 63152 42109 = 0 := by decide
example : lifted 11 0 0 500 0 500 500 2550 5000 26423 12330 = 500 := by decide
example : lifted 11 0 0 136 500 136 70 5939 8144 8029 54396 = 135 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 5631 2192 = 499 := by decide
example : lifted 11 255 0 500 500 500 25 2550 5000 2718 10161 = 500 := by decide
example : lifted 11 0 0 153 500 153 132 2149 2434 32232 20983 = 152 := by decide
example : lifted 11 0 9 500 500 500 499 2550 65535 41296 55311 = 500 := by decide
example : lifted 0 0 127 500 65535 501 499 2550 5000 21922 19831 = 500 := by decide
example : lifted 11 0 0 497 500 497 141 5675 7411 43364 27708 = 496 := by decide
example : lifted 10 0 8 26 500 500 499 2550 5000 3445 34673 = 26 := by decide
example : lifted 11 0 8 500 500 501 499 2550 5000 38358 57965 = 500 := by decide
example : lifted 11 0 0 214 500 214 66 7598 8314 59721 40176 = 213 := by decide
example : lifted 255 0 0 500 500 500 499 2550 65534 2379 62772 = 500 := by decide
example : lifted 255 0 0 500 500 500 499 10000 65535 15751 15534 = 500 := by decide
example : lifted 11 0 0 84 500 84 63 6287 8141 34336 30446 = 83 := by decide
example : lifted 11 0 0 500 65535 500 499 0 5000 38251 49607 = 500 := by decide
example : lifted 11 0 1 500 65535 500 499 2550 5000 15634 58100 = 500 := by decide
example : lifted 11 0 0 147 500 147 8 5271 6709 38815 61414 = 146 := by decide
example : lifted 10 0 0 500 500 501 499 2550 5000 22746 3215 = 500 := by decide
example : lifted 11 0 1 500 499 500 499 0 2550 18842 26255 = 500 := by decide
example : lifted 11 0 0 148 500 148 78 6091 7487 30980 25272 = 147 := by decide
example : lifted 11 0 0 500 0 65535 499 2550 5000 42524 26371 = 500 := by decide
example : lifted 11 255 0 500 500 500 499 2550 2649 25439 63898 = 500 := by decide
example : lifted 11 0 0 109 500 109 7 554 3508 45207 61218 = 108 := by decide
example : lifted 11 0 0 25 500 499 499 2550 2550 53937 36635 = 25 := by decide
example : lifted 255 0 9 0 500 500 499 2550 5000 43881 29317 = 0 := by decide
example : lifted 11 0 0 271 500 271 110 8408 11249 40066 57496 = 270 := by decide
example : lifted 11 0 0 26 500 500 499 2550 5000 50298 58915 = 26 := by decide
example : lifted 11 0 0 501 500 500 499 1 5000 19251 64449 = 501 := by decide
example : lifted 11 0 0 243 500 243 159 1328 4060 37715 15838 = 242 := by decide
example : lifted 0 0 0 500 500 500 499 2550 2550 958 39068 = 500 := by decide
example : lifted 0 0 0 500 499 500 499 2550 5000 43228 40010 = 500 := by decide
example : lifted 11 0 0 249 500 249 220 4485 4860 1981 39969 = 248 := by decide
example : lifted 12 1 0 500 500 500 499 2550 5000 12651 23301 = 500 := by decide
example : lifted 11 255 1 500 500 500 25 2550 5000 57617 54758 = 500 := by decide
example : lifted 11 0 0 121 500 121 115 8293 9301 56291 4957 = 120 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 39781 54870 = 499 := by decide
example : lifted 11 0 0 501 500 500 500 1 5000 40660 1016 = 501 := by decide
example : lifted 11 0 0 71 500 71 17 1284 2822 35871 55982 = 70 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 28169 16564 = 499 := by decide
example : lifted 11 0 0 500 500 0 65535 2550 1141 46227 57519 = 500 := by decide
example : lifted 11 0 0 230 500 230 171 1226 1640 27309 33005 = 229 := by decide
example : lifted 11 0 0 500 500 500 499 2550 1141 50232 5639 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 65535 19384 38564 = 500 := by decide
example : lifted 11 0 0 414 500 414 176 8973 9713 14841 33953 = 413 := by decide
example : lifted 11 0 0 500 500 499 499 2550 5000 50599 18770 = 500 := by decide
example : lifted 11 0 0 500 500 500 0 2550 5000 27992 39136 = 499 := by decide
example : lifted 11 0 0 464 500 464 203 1364 2608 53599 20307 = 463 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 17525 62510 = 499 := by decide
example : lifted 11 0 255 500 500 500 499 2550 5000 23308 8476 = 500 := by decide
example : lifted 11 0 0 74 500 74 47 3224 4843 33636 32076 = 73 := by decide
example : lifted 11 0 0 0 500 65535 499 2550 5000 63002 48581 = 0 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 19151 44470 = 499 := by decide
example : lifted 11 0 0 481 500 481 114 7280 9126 46881 53497 = 480 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 57653 17992 = 499 := by decide
example : lifted 11 0 8 500 501 25 499 2550 5000 16549 1842 = 500 := by decide
example : lifted 11 0 0 178 500 178 44 1338 3816 14027 36793 = 177 := by decide
example : lifted 11 0 0 25 500 500 499 9999 5000 34016 36948 = 25 := by decide
example : lifted 11 0 0 499 500 500 499 2550 5000 3263 17812 = 499 := by decide
example : lifted 11 0 0 455 500 455 338 6415 7524 53739 64685 = 454 := by decide
example : lifted 11 0 0 500 500 500 65535 10001 1141 42943 41411 = 500 := by decide
example : lifted 11 0 255 500 500 500 499 2550 5000 31387 8319 = 500 := by decide
example : lifted 11 0 0 313 500 313 155 7329 9338 24695 5028 = 312 := by decide
example : lifted 255 1 0 500 501 65535 25 2550 5000 56576 51204 = 500 := by decide
example : lifted 11 0 127 500 500 500 499 2550 5000 22527 21313 = 500 := by decide
example : lifted 11 0 0 132 500 132 82 7050 8842 47998 39200 = 131 := by decide
example : lifted 11 0 0 501 500 65535 499 1 5000 29826 48692 = 501 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 51533 26780 = 499 := by decide
example : lifted 11 0 0 287 500 287 65 9963 12095 4727 14437 = 286 := by decide
example : lifted 11 255 0 500 500 65535 499 2550 5000 32024 7296 = 500 := by decide
example : lifted 11 1 0 500 501 500 499 2550 2650 52632 12099 = 500 := by decide
example : lifted 11 0 0 462 500 462 361 4370 4634 23704 43735 = 461 := by decide
example : lifted 11 0 0 25 500 500 499 2550 65534 57774 22695 = 25 := by decide
example : lifted 255 0 0 500 65535 0 499 2550 5000 48946 6771 = 500 := by decide
example : lifted 11 0 0 132 500 132 6 8758 11237 22384 41613 = 131 := by decide
example : lifted 11 1 8 500 500 500 65535 2550 5000 13859 25293 = 500 := by decide
example : lifted 11 0 0 500 65535 500 499 2550 5000 59715 1392 = 500 := by decide
example : lifted 11 0 0 148 500 148 108 6040 6824 30463 40719 = 147 := by decide
example : lifted 11 255 0 24 500 500 499 2550 5000 11901 21554 = 24 := by decide
example : lifted 11 1 127 500 500 500 499 2550 299 27451 63054 = 500 := by decide
example : lifted 11 0 0 347 500 347 110 9533 11441 31430 46194 = 346 := by decide
example : lifted 11 0 0 500 500 501 500 2550 5000 33227 54395 = 500 := by decide
example : lifted 11 1 0 500 501 500 499 2550 5000 6966 494 = 500 := by decide
example : lifted 11 0 0 306 500 306 69 6506 9012 37682 30221 = 305 := by decide
example : lifted 11 0 0 500 0 500 499 2550 5000 21572 19822 = 500 := by decide
example : lifted 11 0 0 500 499 500 499 2550 299 58806 63040 = 500 := by decide
example : lifted 11 0 0 246 500 246 200 1366 4088 11758 57469 = 245 := by decide
example : lifted 11 0 0 500 499 500 499 2550 5000 49022 28455 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 27735 50457 = 499 := by decide
example : lifted 11 0 0 208 500 208 72 8791 9580 27134 35083 = 207 := by decide
example : lifted 11 255 0 500 500 500 499 2550 2651 17330 28108 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 43710 13814 = 499 := by decide
example : lifted 11 0 0 342 500 342 249 1183 3043 50923 57124 = 341 := by decide
example : lifted 11 0 9 500 65535 25 499 2550 5000 56122 57954 = 500 := by decide
example : lifted 11 0 0 0 500 500 0 2550 2651 26054 17100 = 0 := by decide
example : lifted 11 0 0 34 500 34 8 9591 11733 16824 51745 = 33 := by decide
example : lifted 11 0 0 500 500 501 499 2550 2649 60219 48316 = 500 := by decide
example : lifted 11 1 0 500 0 501 499 2550 5000 27833 43767 = 500 := by decide
example : lifted 11 0 0 204 500 204 55 5045 7839 55190 31068 = 203 := by decide
example : lifted 11 0 0 500 500 500 499 65535 5000 55901 1773 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 16600 52474 = 499 := by decide
example : lifted 11 0 0 36 500 36 29 1264 1846 44434 40345 = 35 := by decide
example : lifted 11 0 0 500 501 500 499 2550 2651 28140 63223 = 500 := by decide
example : lifted 11 0 9 500 499 500 25 10000 5000 41265 47976 = 500 := by decide
example : lifted 11 0 0 174 500 174 122 6434 7634 49843 27799 = 173 := by decide
example : lifted 0 0 0 500 500 25 499 2550 0 42477 55456 = 500 := by decide
example : lifted 255 0 1 500 65535 500 499 2550 5000 49326 17082 = 500 := by decide
example : lifted 11 0 0 414 500 414 278 3 3031 17830 5189 = 413 := by decide
example : lifted 11 255 0 500 65535 499 499 2550 65535 61072 13197 = 500 := by decide
example : lifted 11 1 0 500 65535 500 499 10001 5000 41425 34620 = 500 := by decide
example : lifted 11 0 0 427 500 427 180 2763 3283 37251 26614 = 426 := by decide
example : lifted 0 0 0 500 500 0 24 2550 5000 46500 33078 = 500 := by decide
example : lifted 0 0 0 500 500 500 499 2550 299 60899 42642 = 500 := by decide
example : lifted 11 0 0 113 500 113 79 8756 10928 51710 41568 = 112 := by decide
example : lifted 11 0 0 500 0 500 499 1 2550 37768 60239 = 500 := by decide
example : lifted 11 0 0 500 500 500 65535 65535 5000 49847 26376 = 500 := by decide
example : lifted 11 0 0 425 500 425 140 7093 9842 29821 515 = 424 := by decide
example : lifted 11 0 0 500 500 0 0 2550 5000 20322 35497 = 500 := by decide
example : lifted 11 0 0 0 500 500 499 65535 5000 51050 20830 = 0 := by decide
example : lifted 11 0 0 193 500 193 154 9496 10999 42756 12673 = 192 := by decide
example : lifted 10 0 0 500 500 500 500 0 5000 18700 42638 = 500 := by decide
example : lifted 11 0 0 500 500 0 65535 1 65535 2392 43898 = 500 := by decide
example : lifted 11 0 0 222 500 222 83 6652 9146 47507 34431 = 221 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 19525 35586 = 499 := by decide
example : lifted 11 0 0 499 500 500 499 2550 5000 13070 46638 = 499 := by decide
example : lifted 11 0 0 43 500 43 38 5488 8231 47970 21957 = 42 := by decide
example : lifted 11 0 0 500 500 500 499 9999 5000 24529 49579 = 500 := by decide
example : lifted 11 0 0 500 65535 25 499 2550 5000 37110 59342 = 500 := by decide
example : lifted 11 0 0 102 500 102 49 3266 3571 65087 50882 = 101 := by decide
example : lifted 11 0 0 0 499 500 499 2550 5000 60834 18959 = 0 := by decide
example : lifted 11 0 9 500 500 25 501 2550 1141 1588 2309 = 500 := by decide
example : lifted 11 0 0 168 500 168 84 2953 4210 12687 64057 = 167 := by decide
example : lifted 255 0 9 499 500 0 65535 2550 5000 41178 52764 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 44317 59754 = 499 := by decide
example : lifted 11 0 0 177 500 177 84 6183 7120 26234 45552 = 176 := by decide
example : lifted 11 0 0 500 65535 500 500 9999 5000 6342 2241 = 500 := by decide
example : lifted 10 0 0 500 500 500 499 2550 5000 14855 9683 = 500 := by decide
example : lifted 11 0 0 212 500 212 123 4069 4331 4866 49940 = 211 := by decide
example : lifted 11 0 0 500 500 0 499 2550 5000 34607 46118 = 500 := by decide
example : lifted 11 0 127 500 65535 500 500 2550 1141 15864 46440 = 500 := by decide
example : lifted 11 0 0 245 500 245 171 3476 4007 33967 54003 = 244 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 24857 39937 = 499 := by decide
example : lifted 11 0 0 25 500 500 499 2550 299 43714 18716 = 25 := by decide
example : lifted 11 0 0 399 500 399 169 8833 11411 6303 50478 = 398 := by decide
example : lifted 255 0 0 500 500 500 499 2550 5000 5528 10250 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 25134 17870 = 499 := by decide
example : lifted 11 0 0 492 500 492 386 3596 5984 32670 5705 = 491 := by decide
example : lifted 11 0 127 500 500 500 65535 2550 299 24188 12812 = 500 := by decide
example : lifted 11 0 0 500 500 0 499 2550 5000 59946 10239 = 500 := by decide
example : lifted 11 0 0 111 500 111 0 3013 4158 4007 2064 = 110 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 37708 9985 = 499 := by decide
example : lifted 11 0 0 500 500 500 500 2550 5000 6270 48176 = 500 := by decide
example : lifted 11 0 0 492 500 492 145 6002 8172 20677 39716 = 491 := by decide
example : lifted 10 0 0 500 500 501 0 2550 0 52971 18162 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 1865 62782 = 499 := by decide
example : lifted 11 0 0 358 500 358 196 2495 4578 39509 25266 = 357 := by decide
example : lifted 12 0 8 499 500 500 499 2550 5000 63738 47011 = 499 := by decide
example : lifted 11 0 0 500 500 0 499 2550 5000 22577 21682 = 500 := by decide
example : lifted 11 0 0 87 500 87 7 9848 10905 19957 7709 = 86 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 55211 64257 = 499 := by decide
example : lifted 11 255 0 500 500 500 499 2550 5000 21856 46905 = 500 := by decide
example : lifted 11 0 0 378 500 378 139 3444 4452 53192 18670 = 377 := by decide
example : lifted 10 0 0 500 500 500 65535 2550 5000 37748 23053 = 500 := by decide
example : lifted 11 0 255 500 500 500 499 2550 2550 879 63041 = 500 := by decide
example : lifted 11 0 0 75 500 75 60 4873 7903 57432 30551 = 74 := by decide
example : lifted 11 0 0 25 500 500 499 0 5000 41012 23140 = 25 := by decide
example : lifted 11 0 0 500 500 500 499 9999 299 19096 53853 = 500 := by decide
example : lifted 11 0 0 259 500 259 3 1223 4198 29757 14087 = 258 := by decide
example : lifted 11 1 0 65535 65535 500 499 2550 5000 40083 63815 = 65535 := by decide
example : lifted 11 0 0 500 500 500 499 65535 5000 17170 27903 = 500 := by decide
example : lifted 11 0 0 399 500 399 260 9315 10227 19297 20373 = 398 := by decide
example : lifted 11 0 0 500 501 500 0 2550 5000 63874 2890 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 1 2550 39243 7405 = 499 := by decide
example : lifted 11 0 0 352 500 352 237 5896 7084 40211 52745 = 351 := by decide
example : lifted 11 0 0 500 500 500 499 10001 5000 49507 38338 = 500 := by decide
example : lifted 11 0 0 500 500 500 501 1 65534 37848 43996 = 500 := by decide
example : lifted 11 0 0 426 500 426 43 5740 8135 47805 61325 = 425 := by decide
example : lifted 11 0 9 500 500 500 500 2550 5000 8080 33744 = 500 := by decide
example : lifted 11 0 0 500 500 65535 499 2550 5000 14562 39685 = 500 := by decide
example : lifted 11 0 0 370 500 370 218 9443 12019 63133 41147 = 369 := by decide
example : lifted 11 0 9 500 500 500 501 9999 5000 17892 3677 = 500 := by decide
example : lifted 11 0 0 500 500 499 499 2550 5000 62569 21540 = 500 := by decide
example : lifted 11 0 0 499 500 499 169 2547 3659 41271 64312 = 498 := by decide
example : lifted 11 0 9 500 500 500 499 2550 5000 17561 30266 = 500 := by decide
example : lifted 11 0 0 500 499 500 24 2550 5000 48631 31677 = 500 := by decide
example : lifted 11 0 0 462 500 462 388 7069 8351 20101 57603 = 461 := by decide
example : lifted 11 255 0 500 500 500 499 2550 5000 721 37172 = 500 := by decide
example : lifted 11 0 0 500 500 65535 499 2550 2649 13384 41397 = 500 := by decide
example : lifted 11 0 0 226 500 226 195 8149 10773 19113 44720 = 225 := by decide
example : lifted 11 0 0 500 500 500 65535 2550 65534 62738 33393 = 500 := by decide
example : lifted 11 0 0 500 500 500 65535 2550 2649 59766 58679 = 500 := by decide
example : lifted 11 0 0 50 500 50 1 5110 5558 16567 22666 = 49 := by decide
example : lifted 11 0 0 499 500 500 499 2550 1141 60541 3293 = 499 := by decide
example : lifted 10 0 0 500 500 500 499 2550 5000 36447 9737 = 500 := by decide
example : lifted 11 0 0 172 500 172 129 9460 12433 33129 24892 = 171 := by decide
example : lifted 11 0 0 500 500 500 499 10000 5000 39982 37218 = 500 := by decide
example : lifted 11 0 0 24 499 500 499 10001 5000 51603 15701 = 24 := by decide
example : lifted 11 0 0 351 500 351 100 3050 3412 28577 32147 = 350 := by decide
example : lifted 11 0 0 500 500 500 499 10000 5000 29205 40677 = 500 := by decide
example : lifted 10 0 0 24 500 500 499 2550 5000 26160 35279 = 24 := by decide
example : lifted 11 0 0 275 500 275 115 9597 11635 14328 47011 = 274 := by decide
example : lifted 11 255 0 500 500 500 501 2550 5000 54234 38174 = 500 := by decide
example : lifted 11 0 0 500 500 500 0 2550 5000 52614 47035 = 499 := by decide
example : lifted 11 0 0 209 500 209 157 1011 3413 7200 36137 = 208 := by decide
example : lifted 11 1 0 500 500 25 24 2550 5000 37154 37828 = 500 := by decide
example : lifted 11 0 0 500 500 500 24 2550 5000 23057 24221 = 499 := by decide
example : lifted 11 0 0 324 500 324 39 2074 3031 6017 52180 = 323 := by decide
example : lifted 11 0 0 500 499 0 499 2550 5000 13686 15727 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 8933 16859 = 499 := by decide
example : lifted 11 0 0 306 500 306 40 2041 2712 17533 61919 = 305 := by decide
example : lifted 0 0 8 25 0 500 499 2550 299 63032 2754 = 25 := by decide
example : lifted 12 0 0 501 500 500 499 2550 5000 36196 3962 = 501 := by decide
example : lifted 11 0 0 263 500 263 29 5211 7486 44249 34529 = 262 := by decide
example : lifted 11 1 0 0 500 501 499 2550 5000 37600 33806 = 0 := by decide
example : lifted 11 0 8 500 500 500 499 2550 5000 50182 57578 = 500 := by decide
example : lifted 11 0 0 399 500 399 13 2010 2512 3372 6118 = 398 := by decide
example : lifted 11 0 0 500 500 500 501 2550 5000 46317 61556 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 28809 19776 = 499 := by decide
example : lifted 11 0 0 430 500 430 16 2730 3461 59108 32245 = 429 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 47119 22805 = 499 := by decide
example : lifted 255 0 0 500 500 500 499 2550 5000 43456 62243 = 500 := by decide
example : lifted 11 0 0 219 500 219 177 7726 8761 32551 61395 = 218 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 19555 17527 = 499 := by decide
example : lifted 11 1 9 500 500 500 499 2550 1141 24077 13120 = 500 := by decide
example : lifted 11 0 0 258 500 258 218 572 3343 30392 58416 = 257 := by decide
example : lifted 11 0 0 500 500 500 0 2550 5000 8692 24515 = 499 := by decide
example : lifted 11 0 0 0 500 500 25 2550 5000 59691 61730 = 0 := by decide
example : lifted 11 0 0 228 500 228 188 1371 1526 39504 15806 = 227 := by decide
example : lifted 11 0 255 65535 65535 500 499 2550 2650 7437 41680 = 65535 := by decide
example : lifted 11 0 0 500 500 501 499 2550 5000 42783 52393 = 500 := by decide
example : lifted 11 0 0 316 500 316 227 1421 3115 63186 65329 = 315 := by decide
example : lifted 11 0 0 500 500 499 499 2550 5000 32295 18093 = 500 := by decide
example : lifted 11 0 0 500 500 0 499 2550 5000 11871 34116 = 500 := by decide
example : lifted 11 0 0 68 500 68 61 8518 8776 37438 12250 = 67 := by decide
example : lifted 0 0 0 500 500 500 0 2550 5000 48883 57571 = 500 := by decide
example : lifted 11 0 0 501 501 500 499 2550 5000 46936 19958 = 501 := by decide
example : lifted 11 0 0 74 500 74 23 7001 7640 5771 59359 = 73 := by decide
example : lifted 11 0 0 500 500 500 499 65535 5000 18170 50398 = 500 := by decide
example : lifted 11 0 0 65535 500 500 499 2550 5000 20379 559 = 65535 := by decide
example : lifted 11 0 0 190 500 190 4 4694 6850 54661 7966 = 189 := by decide
example : lifted 11 0 1 500 500 25 499 0 5000 8990 64182 = 500 := by decide
example : lifted 11 0 127 500 65535 501 499 2550 5000 14206 16427 = 500 := by decide
example : lifted 11 0 0 234 500 234 138 6368 9032 56958 51296 = 233 := by decide
example : lifted 10 1 0 500 499 500 499 2550 2649 12540 63909 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 10000 5000 28849 53519 = 500 := by decide
example : lifted 11 0 0 36 500 36 11 5194 5416 23783 4268 = 35 := by decide
example : lifted 10 0 0 500 500 500 499 10001 5000 33249 38609 = 500 := by decide
example : lifted 10 0 0 500 500 25 499 2550 299 58291 50100 = 500 := by decide
example : lifted 11 0 0 43 500 43 8 4000 4953 10069 39612 = 42 := by decide
example : lifted 12 0 0 500 500 25 499 9999 5000 61603 32553 = 500 := by decide
example : lifted 11 0 0 500 500 25 499 2550 5000 59533 17127 = 500 := by decide
example : lifted 11 0 0 317 500 317 261 1685 2130 6343 48748 = 316 := by decide
example : lifted 11 0 0 500 500 500 0 2550 299 23991 63149 = 500 := by decide
example : lifted 11 0 0 24 500 500 499 2550 5000 2974 59154 = 24 := by decide
example : lifted 11 0 0 407 500 407 263 6580 9352 35502 13006 = 406 := by decide
example : lifted 11 0 0 500 500 500 501 2550 2651 25118 21327 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 40936 40313 = 499 := by decide
example : lifted 11 0 0 109 500 109 33 5136 8046 50962 31666 = 108 := by decide
example : lifted 11 0 0 500 500 500 499 2550 65534 41314 50429 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 9788 55285 = 499 := by decide
example : lifted 11 0 0 96 500 96 7 7555 9886 24660 28156 = 95 := by decide
example : lifted 11 0 0 500 500 500 499 10001 5000 61556 36276 = 500 := by decide
example : lifted 11 1 0 500 500 500 499 2550 2651 17830 64470 = 500 := by decide
example : lifted 11 0 0 47 500 47 17 6593 8183 13925 29761 = 46 := by decide
example : lifted 11 255 0 500 500 500 499 2550 5000 62583 3236 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 19540 36330 = 499 := by decide
example : lifted 11 0 0 163 500 163 24 493 1147 11014 60127 = 162 := by decide
example : lifted 10 0 0 0 500 500 65535 2550 5000 39545 2979 = 0 := by decide
example : lifted 11 0 0 500 0 500 499 2550 5000 19625 30578 = 500 := by decide
example : lifted 11 0 0 392 500 392 72 2487 3164 34204 7322 = 391 := by decide
example : lifted 11 0 0 500 499 25 499 9999 5000 38909 9190 = 500 := by decide
example : lifted 11 0 0 500 500 25 499 10001 5000 37427 40966 = 500 := by decide
example : lifted 11 0 0 134 500 134 32 4246 5591 54318 28645 = 133 := by decide
example : lifted 11 0 0 500 0 500 500 2550 0 63979 56724 = 500 := by decide
example : lifted 11 0 9 500 500 500 24 10001 2550 758 11159 = 500 := by decide
example : lifted 11 0 0 301 500 301 123 7659 8022 53375 53375 = 300 := by decide
example : lifted 11 0 0 25 500 500 499 2550 5000 39477 58055 = 25 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 52858 16389 = 499 := by decide
example : lifted 11 0 0 256 500 256 129 5940 7902 51692 58990 = 255 := by decide
example : lifted 11 0 0 500 500 500 499 2550 299 48110 23242 = 500 := by decide
example : lifted 11 1 9 500 500 501 499 2550 5000 36026 4149 = 500 := by decide
example : lifted 11 0 0 233 500 233 200 615 3617 23403 12394 = 232 := by decide
example : lifted 11 0 127 0 500 500 499 2550 5000 48102 46083 = 0 := by decide
example : lifted 11 255 0 500 500 500 499 0 5000 6807 10129 = 500 := by decide
example : lifted 11 0 0 330 500 330 157 2053 4914 57690 50060 = 329 := by decide
example : lifted 11 0 127 500 500 500 499 0 5000 30760 57442 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 31476 16681 = 499 := by decide
example : lifted 11 0 0 71 500 71 28 7039 7458 6265 64048 = 70 := by decide
example : lifted 11 0 0 500 500 499 499 9999 2651 17551 62372 = 500 := by decide
example : lifted 11 0 0 500 501 500 25 2550 2650 23082 11969 = 500 := by decide
example : lifted 11 0 0 284 500 284 203 6288 6622 60492 32610 = 283 := by decide
example : lifted 11 0 0 500 500 501 499 2550 5000 56665 46515 = 500 := by decide
example : lifted 0 1 0 500 500 0 499 2550 5000 57196 49633 = 500 := by decide
example : lifted 11 0 0 373 500 373 186 3582 4985 46846 54646 = 372 := by decide
example : lifted 11 0 0 24 500 500 499 2550 5000 12742 34856 = 24 := by decide
example : lifted 11 0 0 500 500 500 0 65535 2550 30657 58001 = 500 := by decide
example : lifted 11 0 0 163 500 163 46 6181 6669 3264 19692 = 162 := by decide
example : lifted 11 255 0 65535 500 65535 25 2550 5000 8300 18557 = 65535 := by decide
example : lifted 11 0 0 500 501 25 499 2550 5000 26927 36140 = 500 := by decide
example : lifted 11 0 0 250 500 250 28 2873 5179 57379 52574 = 249 := by decide
example : lifted 11 0 0 500 500 65535 499 65535 5000 16066 44468 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 2649 42640 14080 = 500 := by decide
example : lifted 11 0 0 483 500 483 303 9407 9803 61054 27320 = 482 := by decide
example : lifted 11 1 0 500 499 500 499 2550 5000 7211 64773 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 30359 33699 = 499 := by decide
example : lifted 11 0 0 184 500 184 163 4730 7683 32513 15832 = 183 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 42471 12859 = 499 := by decide
example : lifted 11 0 0 500 499 500 499 2550 5000 40915 11031 = 500 := by decide
example : lifted 11 0 0 228 500 228 209 1360 4390 9359 31958 = 227 := by decide
example : lifted 11 0 0 65535 500 500 499 2550 5000 30544 1710 = 65535 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 13369 1797 = 499 := by decide
example : lifted 11 0 0 115 500 115 70 1228 3857 56292 28458 = 114 := by decide
example : lifted 11 0 1 0 500 500 499 2550 5000 12568 11199 = 0 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 54852 32855 = 499 := by decide
example : lifted 11 0 0 394 500 394 20 6874 7698 4888 44781 = 393 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 9304 9003 = 499 := by decide
example : lifted 10 0 0 500 500 500 499 2550 5000 50344 54547 = 500 := by decide
example : lifted 11 0 0 456 500 456 352 6443 6585 59005 6505 = 455 := by decide
example : lifted 11 0 0 500 500 500 499 10001 65534 29537 54909 = 500 := by decide
example : lifted 11 0 0 500 500 0 499 2550 5000 46042 20477 = 500 := by decide
example : lifted 11 0 0 292 500 292 161 723 1090 20346 22032 = 291 := by decide
example : lifted 11 255 0 0 500 500 499 2550 5000 38883 38121 = 0 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 59557 17950 = 499 := by decide
example : lifted 11 0 0 83 500 83 75 2306 4112 62898 38379 = 82 := by decide
example : lifted 0 0 0 500 500 500 500 2550 1141 21888 16032 = 500 := by decide
example : lifted 11 0 0 0 500 65535 499 9999 5000 34786 52131 = 0 := by decide
example : lifted 11 0 0 426 500 426 183 7642 10240 57325 11298 = 425 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 7090 31212 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 30315 34700 = 499 := by decide
example : lifted 11 0 0 36 500 36 21 1564 3671 29296 17980 = 35 := by decide
example : lifted 11 0 0 500 500 499 499 2550 5000 31730 47460 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 15983 24254 = 499 := by decide
example : lifted 11 0 0 96 500 96 27 480 3253 18848 19397 = 95 := by decide
example : lifted 11 255 0 500 500 25 499 2550 5000 1837 33451 = 500 := by decide
example : lifted 11 0 0 65535 501 500 499 2550 5000 50615 52396 = 65535 := by decide
example : lifted 11 0 0 312 500 312 233 3006 4452 57603 60739 = 311 := by decide
example : lifted 12 1 0 500 500 500 499 9999 2550 57703 8961 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 23582 15376 = 499 := by decide
example : lifted 11 0 0 111 500 111 31 707 1309 8144 61174 = 110 := by decide
example : lifted 12 0 0 500 500 500 499 65535 5000 6392 62968 = 500 := by decide
example : lifted 11 0 0 500 499 500 0 2550 2650 145 334 = 500 := by decide
example : lifted 11 0 0 276 500 276 231 1992 3523 65075 59358 = 275 := by decide
example : lifted 11 0 8 500 501 500 499 2550 5000 15371 56238 = 500 := by decide
example : lifted 11 0 0 65535 65535 500 501 2550 2649 55247 50374 = 65535 := by decide
example : lifted 11 0 0 236 500 236 127 6034 6152 3975 39849 = 235 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 5592 37628 = 499 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 7754 38101 = 499 := by decide
example : lifted 11 0 0 33 500 33 1 9677 12748 54677 42503 = 32 := by decide
example : lifted 10 0 0 500 501 500 499 0 5000 53297 56605 = 500 := by decide
example : lifted 11 0 0 25 500 500 499 2550 5000 50961 51077 = 25 := by decide
example : lifted 11 0 0 277 500 277 20 5824 6167 64635 16221 = 276 := by decide
example : lifted 11 0 0 501 501 0 499 2550 65534 16037 30515 = 501 := by decide
example : lifted 10 0 0 24 500 500 499 2550 5000 15525 18275 = 24 := by decide
example : lifted 11 0 0 316 500 316 172 6515 8579 14871 32382 = 315 := by decide
example : lifted 11 255 255 500 500 500 25 2550 2649 46810 30312 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 10001 5000 41959 65376 = 500 := by decide
example : lifted 11 0 0 114 500 114 108 1146 2177 55763 10954 = 113 := by decide
example : lifted 11 0 1 500 501 500 499 2550 1141 16499 20794 = 500 := by decide
example : lifted 11 1 0 500 500 500 499 10000 5000 31333 61938 = 500 := by decide
example : lifted 11 0 0 420 500 420 414 9404 10188 5072 15430 = 419 := by decide
example : lifted 11 0 9 500 500 500 499 65535 5000 10049 38523 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 45729 29330 = 499 := by decide
example : lifted 11 0 0 450 500 450 208 2479 3557 57945 50829 = 449 := by decide
example : lifted 11 0 1 500 500 500 65535 0 5000 45014 56395 = 500 := by decide
example : lifted 11 255 0 500 500 500 499 2550 1141 61731 16380 = 500 := by decide
example : lifted 11 0 0 48 500 48 15 9556 11518 59859 6639 = 47 := by decide
example : lifted 11 0 0 500 500 500 499 10000 5000 462 29243 = 500 := by decide
example : lifted 10 0 0 500 500 500 499 2550 5000 42186 13236 = 500 := by decide
example : lifted 11 0 0 50 500 50 44 8533 10970 39362 18123 = 49 := by decide
example : lifted 11 255 0 500 501 65535 499 2550 5000 26095 9734 = 500 := by decide
example : lifted 11 0 0 500 500 500 499 2550 2550 34712 5290 = 500 := by decide
example : lifted 11 0 0 240 500 240 188 1749 4491 19964 1279 = 239 := by decide
example : lifted 11 0 0 500 500 500 25 0 5000 18784 1806 = 500 := by decide
example : lifted 11 0 8 500 500 500 499 2550 1141 23783 39909 = 500 := by decide
example : lifted 11 0 0 247 500 247 144 8173 11055 36721 56645 = 246 := by decide
example : lifted 11 0 0 500 500 65535 24 2550 5000 46249 59927 = 500 := by decide
example : lifted 11 255 0 25 500 500 499 2550 5000 50407 59895 = 25 := by decide
example : lifted 11 0 0 154 500 154 78 9349 11597 10617 54871 = 153 := by decide
example : lifted 11 1 0 500 500 500 499 2550 5000 10896 57493 = 500 := by decide
example : lifted 11 1 8 500 0 500 499 2550 5000 42856 47062 = 500 := by decide
example : lifted 11 0 0 219 500 219 111 3010 4128 9061 14886 = 218 := by decide
example : lifted 11 0 0 501 65535 500 0 2550 5000 42412 47002 = 501 := by decide
example : lifted 11 0 0 500 0 500 24 2550 0 16070 8099 = 500 := by decide
example : lifted 11 0 0 240 500 240 123 7653 9414 63369 39046 = 239 := by decide
example : lifted 11 0 0 25 500 500 499 2550 5000 4108 12820 = 25 := by decide
example : lifted 0 0 0 500 500 500 499 2550 5000 58010 19023 = 500 := by decide
example : lifted 11 0 0 83 500 83 17 7462 8799 16586 23522 = 82 := by decide
example : lifted 11 0 8 500 500 500 24 9999 2650 42817 764 = 500 := by decide
example : lifted 11 0 9 25 500 0 499 2550 5000 55375 20043 = 25 := by decide
example : lifted 11 0 0 329 500 329 226 7682 8087 7525 52776 = 328 := by decide
example : lifted 255 0 0 500 499 500 499 2550 5000 4994 465 = 500 := by decide
example : lifted 10 0 0 500 500 500 499 2550 2550 25265 5007 = 500 := by decide
example : lifted 11 0 0 425 500 425 284 8658 9818 38258 2533 = 424 := by decide
example : lifted 11 0 9 500 500 500 65535 2550 5000 62072 19048 = 500 := by decide
example : lifted 11 0 0 500 500 501 499 10001 5000 26355 27388 = 500 := by decide
example : lifted 11 0 0 43 500 43 24 7379 10128 32964 43512 = 42 := by decide
example : lifted 11 0 255 500 500 500 499 2550 5000 52412 53827 = 500 := by decide
example : lifted 11 0 255 500 500 500 499 2550 5000 4629 64074 = 500 := by decide
example : lifted 11 0 0 302 500 302 46 7428 8578 20536 57068 = 301 := by decide
example : lifted 11 1 255 500 500 500 499 2550 5000 58425 13966 = 500 := by decide
example : lifted 11 0 127 500 500 500 499 1 1141 47237 18345 = 500 := by decide
example : lifted 11 0 0 90 500 90 74 4561 5981 26887 23347 = 89 := by decide
example : lifted 11 0 0 500 500 500 499 2550 5000 21097 55605 = 499 := by decide
example : lifted 255 0 0 499 501 500 500 2550 5000 64620 28554 = 499 := by decide
example : lifted 11 0 0 251 500 251 38 7037 7611 7759 45098 = 250 := by decide
example : lifted 11 0 1 500 65535 499 499 65535 5000 39575 11654 = 500 := by decide
example : lifted 11 255 9 499 500 500 499 2550 5000 29632 24235 = 499 := by decide
example : lifted 11 0 0 238 500 238 55 453 2905 26522 44803 = 237 := by decide
example : lifted 11 0 0 500 500 499 24 2550 5000 23595 53566 = 500 := by decide
example : lifted 11 1 0 500 500 500 499 2550 5000 11619 57564 = 500 := by decide
example : lifted 11 0 0 165 500 165 161 5427 6201 22653 33741 = 164 := by decide
example : lifted 11 0 127 500 500 500 499 2550 5000 65477 21049 = 500 := by decide
example : lifted 11 0 9 500 65535 500 499 2550 0 16727 34115 = 500 := by decide
example : lifted 11 0 0 349 500 349 177 5847 8652 31803 15076 = 348 := by decide
example : lifted 11 0 0 500 499 25 499 2550 5000 46133 40090 = 500 := by decide
example : lifted 11 0 9 499 500 25 499 0 5000 60018 11029 = 499 := by decide
example : lifted 11 0 0 102 500 102 26 6468 8495 63622 32102 = 101 := by decide
example : lifted 10 255 0 500 501 500 499 2550 5000 34757 46582 = 500 := by decide
end R17Decay
